import psutil
import asyncio
import socket
import logging
import json
import os
from typing import Optional, Callable, Dict


class PortTrafficMonitor:
    def __init__(self, port: int, update_callback: Optional[Callable[[dict], None]] = None):
        """
        Initializes the traffic monitor for a specific port.

        Args:
            port: Port number to monitor.
            update_callback: Callback function to handle traffic updates.
        """
        self.port = port
        self.update_callback = update_callback
        self.running = False
        self._previous_stats = {}
        self._previous_net_io = None
        self._stats_file = f'traffic_stats_{port}.json'
        self._accumulated_traffic = self._load_stats()

    def reset_counters(self):
        """
        Resets all traffic counters to zero and saves the zeroed state.

        This includes:
        - Accumulated traffic statistics
        - Previous network I/O counters
        - Previous connection statistics
        """
        self._accumulated_traffic = {'bytes_sent': 0, 'bytes_recv': 0}
        self._previous_stats = {}
        self._previous_net_io = None
        self._save_stats()

        if self.update_callback:
            # Notify callback about the reset
            self.update_callback({
                'bytes_sent': 0,
                'bytes_recv': 0,
                'total_bytes_sent': 0,
                'total_bytes_recv': 0,
                'active_connections': 0,
                'upload_speed': 0,
                'download_speed': 0,
                'connections': {}
            })

    def _load_stats(self) -> dict:
        """
        Loads saved traffic statistics from a file.

        Returns:
            A dictionary containing accumulated traffic statistics.
        """
        try:
            if os.path.exists(self._stats_file):
                with open(self._stats_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading stats: {e}")
        return {'bytes_sent': 0, 'bytes_recv': 0}

    def _save_stats(self):
        """
        Saves accumulated traffic statistics to a file.
        """
        try:
            with open(self._stats_file, 'w') as f:
                json.dump(self._accumulated_traffic, f)
        except Exception as e:
            logging.error(f"Error saving stats: {e}")

    def get_stats(self) -> dict:
        """
        Возвращает текущую статистику трафика.

        Returns:
            Словарь с данными о трафике, включая скорость и активные соединения.
        """
        # Получаем текущие данные о соединениях и трафике
        connection_stats, total_traffic = self._get_connection_stats()
        current_total = self._calculate_total_traffic(connection_stats, total_traffic)
        stats_with_speed = self._calculate_speed(current_total, 1.0)  # Интервал по умолчанию 1 секунда
        stats_with_speed['connections'] = connection_stats
        return stats_with_speed

    def _get_connection_stats(self) -> Dict[tuple, dict]:
        """
        Retrieves statistics for active connections on the monitored port.

        Returns:
            A dictionary of connection stats and total traffic.
        """
        connection_stats = {}
        try:
            # Retrieve network interface statistics
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

            # Retrieve TCP and UDP connections
            connections = []
            connections.extend(psutil.net_connections(kind='tcp'))
            connections.extend(psutil.net_connections(kind='udp'))

            port_connections = [
                conn for conn in connections
                if (conn.laddr.port == self.port or (
                        hasattr(conn, 'raddr') and conn.raddr and conn.raddr.port == self.port))
                   and (conn.type == socket.SOCK_STREAM or conn.type == socket.SOCK_DGRAM)
                   and (conn.status == 'ESTABLISHED' or conn.type == socket.SOCK_DGRAM)
            ]

            for conn in port_connections:
                conn_id = (
                    f"{conn.laddr.ip}:{conn.laddr.port}",
                    f"{conn.raddr.ip}:{conn.raddr.port}" if hasattr(conn, 'raddr') and conn.raddr else None
                )

                try:
                    process = psutil.Process(conn.pid) if conn.pid else None
                    if process:
                        connection_stats[conn_id] = {
                            'pid': conn.pid,
                            'status': getattr(conn, 'status', 'UNKNOWN'),
                            'type': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logging.warning(f"Process error for connection {conn_id}: {e}")
                    continue

            # Distribute total traffic across active connections
            if connection_stats:
                connections_count = len(connection_stats)
                traffic_per_connection = {
                    'bytes_sent': total_bytes_sent / connections_count,
                    'bytes_recv': total_bytes_recv / connections_count
                }

                for conn_id in connection_stats:
                    connection_stats[conn_id].update(traffic_per_connection)

        except Exception as e:
            logging.error(f"Error getting connection statistics: {e}")

        return connection_stats, {'bytes_sent': total_bytes_sent, 'bytes_recv': total_bytes_recv}

    def _calculate_total_traffic(self, connection_stats: Dict[tuple, dict], total_traffic: dict) -> dict:
        """
        Adds current traffic to accumulated statistics and saves the updated data.

        Args:
            connection_stats: Dictionary of active connection statistics.
            total_traffic: Dictionary of total traffic for the current interval.

        Returns:
            Updated total traffic statistics including accumulated data.
        """
        self._accumulated_traffic['bytes_sent'] += total_traffic['bytes_sent']
        self._accumulated_traffic['bytes_recv'] += total_traffic['bytes_recv']

        self._save_stats()

        return {
            'bytes_sent': total_traffic['bytes_sent'],
            'bytes_recv': total_traffic['bytes_recv'],
            'total_bytes_sent': self._accumulated_traffic['bytes_sent'],
            'total_bytes_recv': self._accumulated_traffic['bytes_recv'],
            'active_connections': len(connection_stats)
        }

    def _calculate_speed(self, current_total: dict, interval: float) -> dict:
        """
        Calculates upload and download speeds.

        Args:
            current_total: Current traffic statistics.
            interval: Monitoring interval in seconds.

        Returns:
            Traffic statistics with upload and download speeds.
        """
        return {
            **current_total,
            'upload_speed': current_total['bytes_sent'] / interval,
            'download_speed': current_total['bytes_recv'] / interval
        }

    async def start_monitoring(self, interval: float = 1.0):
        """
        Starts monitoring traffic for the specified port.

        Args:
            interval: Monitoring interval in seconds.
        """
        self.running = True

        while self.running:
            try:
                connection_stats, total_traffic = self._get_connection_stats()
                current_total = self._calculate_total_traffic(connection_stats, total_traffic)
                stats_with_speed = self._calculate_speed(current_total, interval)
                stats_with_speed['connections'] = connection_stats

                if self.update_callback:
                    self.update_callback(stats_with_speed)

                await asyncio.sleep(interval)

            except Exception as e:
                logging.error(f"Error in traffic monitoring: {e}")
                await asyncio.sleep(interval)

    def stop_monitoring(self):
        """
        Stops monitoring and saves accumulated traffic statistics.
        """
        self.running = False
        self._save_stats()

    @staticmethod
    def format_bytes(bytes_value: float) -> str:
        """
        Converts bytes to a human-readable format.

        Args:
            bytes_value: Number of bytes.

        Returns:
            Formatted string representing the byte value.
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f} TB"
