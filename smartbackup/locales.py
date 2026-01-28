"""
Localization strings for SmartBackup.
Supports English and Spanish.
"""

from typing import Dict

STRINGS: Dict[str, Dict[str, str]] = {
    # Application
    "app_title": {
        "en": "SmartBackup Local",
        "es": "SmartBackup Local"
    },
    "app_subtitle": {
        "en": "Protect your files with ease",
        "es": "Protege tus archivos con facilidad"
    },
    
    # Source/Destination
    "source_folder": {
        "en": "Source Folder",
        "es": "Carpeta de Origen"
    },
    "destination_folder": {
        "en": "Destination Folder",
        "es": "Carpeta de Destino"
    },
    "select_source": {
        "en": "Select source folder...",
        "es": "Seleccionar carpeta de origen..."
    },
    "select_destination": {
        "en": "Select destination folder...",
        "es": "Seleccionar carpeta de destino..."
    },
    "browse": {
        "en": "Browse",
        "es": "Examinar"
    },
    
    # Backup modes
    "backup_mode": {
        "en": "Backup Mode",
        "es": "Modo de Respaldo"
    },
    "mode_full": {
        "en": "Full Backup",
        "es": "Respaldo Completo"
    },
    "mode_incremental": {
        "en": "Incremental Backup",
        "es": "Respaldo Incremental"
    },
    "mode_differential": {
        "en": "Differential Backup",
        "es": "Respaldo Diferencial"
    },
    
    # Mode descriptions
    "mode_full_desc": {
        "en": "Copies ALL files from source to destination. Best for first-time backups.",
        "es": "Copia TODOS los archivos del origen al destino. Ideal para respaldos iniciales."
    },
    "mode_incremental_desc": {
        "en": "Only copies files that changed since the LAST backup (any type). Fastest option.",
        "es": "Solo copia archivos que cambiaron desde el ÚLTIMO respaldo (cualquier tipo). La opción más rápida."
    },
    "mode_differential_desc": {
        "en": "Copies all files changed since the last FULL backup. Balance between speed and simplicity.",
        "es": "Copia todos los archivos que cambiaron desde el último respaldo COMPLETO. Balance entre velocidad y simplicidad."
    },
    
    # Actions
    "backup_now": {
        "en": "Protect Now",
        "es": "Proteger Ahora"
    },
    "cancel": {
        "en": "Cancel",
        "es": "Cancelar"
    },
    "help": {
        "en": "Help",
        "es": "Ayuda"
    },
    "close": {
        "en": "Close",
        "es": "Cerrar"
    },
    
    # Status messages
    "status_ready": {
        "en": "Ready",
        "es": "Listo"
    },
    "status_backing_up": {
        "en": "Backing up...",
        "es": "Respaldando..."
    },
    "status_complete": {
        "en": "Backup completed successfully!",
        "es": "¡Respaldo completado exitosamente!"
    },
    "status_cancelled": {
        "en": "Backup cancelled",
        "es": "Respaldo cancelado"
    },
    "status_error": {
        "en": "Error during backup",
        "es": "Error durante el respaldo"
    },
    "copying_file": {
        "en": "Copying: {filename}",
        "es": "Copiando: {filename}"
    },
    "files_processed": {
        "en": "{count} files processed",
        "es": "{count} archivos procesados"
    },
    "files_copied": {
        "en": "{count} files copied",
        "es": "{count} archivos copiados"
    },
    "files_skipped": {
        "en": "{count} files skipped (unchanged)",
        "es": "{count} archivos omitidos (sin cambios)"
    },
    
    # Errors
    "error_no_source": {
        "en": "Please select a source folder",
        "es": "Por favor selecciona una carpeta de origen"
    },
    "error_no_destination": {
        "en": "Please select a destination folder",
        "es": "Por favor selecciona una carpeta de destino"
    },
    "error_same_folder": {
        "en": "Source and destination cannot be the same",
        "es": "El origen y destino no pueden ser iguales"
    },
    "error_source_not_exists": {
        "en": "Source folder does not exist",
        "es": "La carpeta de origen no existe"
    },
    "error_no_full_backup": {
        "en": "No full backup found. Please run a full backup first.",
        "es": "No se encontró respaldo completo. Por favor ejecuta un respaldo completo primero."
    },
    
    # Help dialog
    "help_title": {
        "en": "Help & Tutorial",
        "es": "Ayuda y Tutorial"
    },
    "help_intro": {
        "en": "SmartBackup helps you protect your important files with smart deduplication.",
        "es": "SmartBackup te ayuda a proteger tus archivos importantes con deduplicación inteligente."
    },
    "help_modes_title": {
        "en": "Understanding Backup Modes",
        "es": "Entendiendo los Modos de Respaldo"
    },
    "help_tip": {
        "en": "💡 Tip: Start with a Full Backup, then use Incremental for daily backups.",
        "es": "💡 Consejo: Comienza con un Respaldo Completo, luego usa Incremental para respaldos diarios."
    },
    
    # Confirmations
    "confirm_backup": {
        "en": "Start backup?",
        "es": "¿Iniciar respaldo?"
    },
    "confirm_backup_msg": {
        "en": "This will backup files from:\n{source}\n\nTo:\n{destination}\n\nMode: {mode}",
        "es": "Esto respaldará archivos desde:\n{source}\n\nHacia:\n{destination}\n\nModo: {mode}"
    },
    
    # Scheduler
    "schedule": {
        "en": "Schedule",
        "es": "Programar"
    },
    "scheduled_backups": {
        "en": "Scheduled Backups",
        "es": "Respaldos Programados"
    },
    "add_schedule": {
        "en": "Add Schedule",
        "es": "Agregar Programación"
    },
    "edit_schedule": {
        "en": "Edit Schedule",
        "es": "Editar Programación"
    },
    "delete_schedule": {
        "en": "Delete Schedule",
        "es": "Eliminar Programación"
    },
    "schedule_name": {
        "en": "Schedule Name",
        "es": "Nombre de Programación"
    },
    "frequency": {
        "en": "Frequency",
        "es": "Frecuencia"
    },
    "freq_once": {
        "en": "Once",
        "es": "Una vez"
    },
    "freq_hourly": {
        "en": "Hourly",
        "es": "Cada hora"
    },
    "freq_daily": {
        "en": "Daily",
        "es": "Diario"
    },
    "freq_weekly": {
        "en": "Weekly",
        "es": "Semanal"
    },
    "freq_monthly": {
        "en": "Monthly",
        "es": "Mensual"
    },
    "time": {
        "en": "Time",
        "es": "Hora"
    },
    "day_of_week": {
        "en": "Day of Week",
        "es": "Día de la Semana"
    },
    "day_of_month": {
        "en": "Day of Month",
        "es": "Día del Mes"
    },
    "monday": {
        "en": "Monday",
        "es": "Lunes"
    },
    "tuesday": {
        "en": "Tuesday",
        "es": "Martes"
    },
    "wednesday": {
        "en": "Wednesday",
        "es": "Miércoles"
    },
    "thursday": {
        "en": "Thursday",
        "es": "Jueves"
    },
    "friday": {
        "en": "Friday",
        "es": "Viernes"
    },
    "saturday": {
        "en": "Saturday",
        "es": "Sábado"
    },
    "sunday": {
        "en": "Sunday",
        "es": "Domingo"
    },
    "next_run": {
        "en": "Next Run",
        "es": "Próxima Ejecución"
    },
    "last_run": {
        "en": "Last Run",
        "es": "Última Ejecución"
    },
    "never": {
        "en": "Never",
        "es": "Nunca"
    },
    "enabled": {
        "en": "Enabled",
        "es": "Habilitado"
    },
    "disabled": {
        "en": "Disabled",
        "es": "Deshabilitado"
    },
    "run_now": {
        "en": "Run Now",
        "es": "Ejecutar Ahora"
    },
    "save": {
        "en": "Save",
        "es": "Guardar"
    },
    "no_schedules": {
        "en": "No scheduled backups configured",
        "es": "No hay respaldos programados"
    },
    "schedule_created": {
        "en": "Schedule created successfully",
        "es": "Programación creada exitosamente"
    },
    "schedule_updated": {
        "en": "Schedule updated successfully",
        "es": "Programación actualizada exitosamente"
    },
    "schedule_deleted": {
        "en": "Schedule deleted",
        "es": "Programación eliminada"
    },
    "confirm_delete_schedule": {
        "en": "Are you sure you want to delete this schedule?",
        "es": "¿Estás seguro de que quieres eliminar esta programación?"
    },
    "scheduled_backup_started": {
        "en": "Scheduled backup started: {name}",
        "es": "Respaldo programado iniciado: {name}"
    },
    "scheduled_backup_complete": {
        "en": "Scheduled backup completed: {name}",
        "es": "Respaldo programado completado: {name}"
    },
    "hour_interval": {
        "en": "Every",
        "es": "Cada"
    },
    "hours": {
        "en": "hours",
        "es": "horas"
    },
    "select_days": {
        "en": "Select Days",
        "es": "Seleccionar Días"
    },
}


def get_string(key: str, lang: str = "en", **kwargs) -> str:
    """
    Get a localized string.
    
    Args:
        key: The string key to look up
        lang: Language code ('en' or 'es')
        **kwargs: Format arguments for the string
    
    Returns:
        The localized string, formatted with any provided arguments
    """
    if key not in STRINGS:
        return key
    
    string_dict = STRINGS[key]
    text = string_dict.get(lang, string_dict.get("en", key))
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text


class Localizer:
    """Helper class for easy localization access."""
    
    def __init__(self, lang: str = "en"):
        self.lang = lang
    
    def __call__(self, key: str, **kwargs) -> str:
        return get_string(key, self.lang, **kwargs)
    
    def set_language(self, lang: str) -> None:
        self.lang = lang
