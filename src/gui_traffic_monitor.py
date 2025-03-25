import psutil
import asyncio
import socket
import logging
import json
import os
from typing import Optional, Callable, Dict, NamedTuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Data type for connection statistics
class ConnectionStats(NamedTuple):
    pid: int
    status: str
    type: str
    bytes_sent: float
    bytes_recv: float


# Data type for overall traffic statistics
class TrafficStats(NamedTuple):
    bytes_sent: float
    bytes_recv: float
    total_bytes_sent: float
    total_bytes_recv: float
    active_connections: int
    upload_speed: float
    download_speed: float
    connections: Dict[tuple, ConnectionStats]


# Class for handling statistics storage
class StatsStorage:
    def __init__(self, port: int):
        self._stats_file = f'traffic_stats_{port}.json'
        self._accumulated_traffic = self._load_stats()

    def _load_stats(self) -> dict:
        try:
            if os.path.exists(self._stats_file):
                with open(self._stats_file, 'r') as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error in {self._stats_file}: {e}")
        except Exception as e:
            logging.error(f"Error loading stats from {self._stats_file}: {e}")
        return {'bytes_sent': 0, 'bytes_recv': 0}

    def _save_stats(self):
        try:
            with open(self._stats_file, 'w') as f:
                json.dump(self._accumulated_traffic, f)
        except Exception as e:
            logging.error(f"Error saving stats to {self._stats_file}: {e}")

    def update(self, bytes_sent: float, bytes_recv: float):
        self._accumulated_traffic['bytes_sent'] += bytes_sent
        self._accumulated_traffic['bytes_recv'] += bytes_recv
        self._save_stats()

    def get_accumulated(self) -> dict:
        return self._accumulated_traffic.copy()


# Main traffic monitoring class
class PortTrafficMonitor:
    def __init__(self, port: int, update_callback: Optional[Callable[[TrafficStats], None]] = None):
        self.port = port
        self.update_callback = update_callback
        self.running = False
        self._previous_net_io = None
        self._storage = StatsStorage(port)

    def reset_counters(self):
        accumulated = self._storage.get_accumulated()
        self._storage.update(-accumulated['bytes_sent'], -accumulated['bytes_recv'])
        self._previous_net_io = None
        if self.update_callback:
            self.update_callback(TrafficStats(
                bytes_sent=0,
                bytes_recv=0,
                total_bytes_sent=0,
                total_bytes_recv=0,
                active_connections=0,
                upload_speed=0,
                download_speed=0,
                connections={}
            ))

    def _get_connection_stats(self) -> Dict[tuple, ConnectionStats]:
        connection_stats = {}
        try:
            net_io = psutil.net_io_counters(pernic=True)
            total_bytes_sent = 0
            total_bytes_recv = 0

            for nic, counters in net_io.items():
                if self._previous_net_io and nic in self._previous_net_io:
                    prev_counters = self._previous_net_io[nic]
                    bytes_sent = counters.bytes_sent - prev_counters.bytes_sent
                    bytes_recv = counters.bytes_recv - prev_counters.bytes_recv
                    total_bytes_sent += max(0, bytes_sent)
                    total_bytes_recv += max(0, bytes_recv)

            self._previous_net_io = net_io

            connections = []
            connections.extend(psutil.net_connections(kind='tcp'))
            connections.extend(psutil.net_connections(kind='udp'))

            port_connections = [
                conn for conn in connections
                if (conn.laddr.port == self.port or (conn.raddr and conn.raddr.port == self.port))
                   and (conn.type == socket.SOCK_STREAM or conn.type == socket.SOCK_DGRAM)
                   and (conn.status == 'ESTABLISHED' or conn.type == socket.SOCK_DGRAM)
            ]

            for conn in port_connections:
                conn_id = (
                    (conn.laddr.ip, conn.laddr.port),
                    (conn.raddr.ip, conn.raddr.port) if conn.raddr else None
                )

                try:
                    process = psutil.Process(conn.pid) if conn.pid else None
                    if process:
                        connection_stats[conn_id] = ConnectionStats(
                            pid=conn.pid,
                            status=getattr(conn, 'status', 'UNKNOWN'),
                            type='TCP' if conn.type == socket.SOCK_STREAM else 'UDP',
                            bytes_sent=0,
                            bytes_recv=0
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logging.warning(f"Process error for connection {conn_id}: {e}")
                    continue

            if connection_stats:
                connections_count = len(connection_stats)
                traffic_per_connection = {
                    'bytes_sent': total_bytes_sent / connections_count,
                    'bytes_recv': total_bytes_recv / connections_count
                }
                for conn_id in connection_stats:
                    connection_stats[conn_id] = connection_stats[conn_id]._replace(
                        bytes_sent=traffic_per_connection['bytes_sent'],
                        bytes_recv=traffic_per_connection['bytes_recv']
                    )

        except psutil.Error as e:
            logging.error(f"psutil error while getting statistics: {e}")
        except Exception as e:
            logging.error(f"Unexpected error while getting statistics: {e}")

        return connection_stats

    def _calculate_total_traffic(self, connection_stats: Dict[tuple, ConnectionStats], total_traffic: dict) -> dict:
        self._storage.update(total_traffic['bytes_sent'], total_traffic['bytes_recv'])
        accumulated = self._storage.get_accumulated()
        return {
            'bytes_sent': total_traffic['bytes_sent'],
            'bytes_recv': total_traffic['bytes_recv'],
            'total_bytes_sent': accumulated['bytes_sent'],
            'total_bytes_recv': accumulated['bytes_recv'],
            'active_connections': len(connection_stats)
        }

    def _calculate_speed(self, current_total: dict, interval: float) -> dict:
        return {
            **current_total,
            'upload_speed': current_total['bytes_sent'] / interval,
            'download_speed': current_total['bytes_recv'] / interval
        }

    async def start_monitoring(self, interval: float = 1.0):
        self.running = True
        while self.running:
            try:
                connection_stats = self._get_connection_stats()
                total_traffic = {
                    'bytes_sent': sum(conn.bytes_sent for conn in connection_stats.values()),
                    'bytes_recv': sum(conn.bytes_recv for conn in connection_stats.values())
                }
                current_total = self._calculate_total_traffic(connection_stats, total_traffic)
                stats_with_speed = self._calculate_speed(current_total, interval)
                traffic_stats = TrafficStats(
                    **stats_with_speed,
                    connections=connection_stats
                )

                if self.update_callback:
                    self.update_callback(traffic_stats)

                await asyncio.sleep(interval)
            except Exception as e:
                logging.error(f"Traffic monitoring error: {e}")
                await asyncio.sleep(interval)

    def stop_monitoring(self):
        self.running = False

    @staticmethod
    def format_bytes(bytes_value: float) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f} TB"
