# Core module - Entry point for all core functionality
# This module provides backward compatibility by importing from the correct enterprise modules

# Import all essential functions from their new locations
from shared.utils.core_utils import (
    log_debug,
    track_function_entry,
    global_state,
    health_check,
    emergency_reset,
    get_current_metrics,
    toggle_debug_mode,
    get_service_status,
    bucket,
    index_endpoint,
    storage_client,
    drive_service,
    initialize_all_services,
    openai_client
)

# Make all functions available at module level for backward compatibility
__all__ = [
    'log_debug',
    'track_function_entry',
    'global_state',
    'health_check',
    'emergency_reset',
    'get_current_metrics',
    'toggle_debug_mode',
    'get_service_status',
    'bucket',
    'index_endpoint',
    'storage_client',
    'drive_service',
    'initialize_all_services',
    'openai_client'
]