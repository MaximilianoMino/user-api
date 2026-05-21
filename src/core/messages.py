# @track_context("core_constants.md")

"""
User-facing messages for the Supabase Auth API

This module contains all user-facing text organized by category
for better maintainability and localization support.
"""


class ErrorMessages:
    """Error messages shown to users"""

    INVALID_CREDENTIALS = "Invalid email or password"
    INVALID_TOKEN = "Invalid authentication token"
    INVALID_TOKEN_MISSING_USER = "Invalid token: missing user identifier"
    USER_NOT_FOUND = "Usuario no encontrado en el sistema"

    LOGOUT_FAILED = "Failed to log out"
    REGISTRATION_FAILED = "Registration failed"
    AUTHENTICATION_FAILED = "Authentication failed"

    # Lotes
    VARIEDAD_NOT_FOUND = "La variedad especificada no existe"
    SUBVARIEDAD_INVALIDA = "La subvariedad no pertenece a la variedad seleccionada"
    TEMPORADA_NOT_FOUND = "La temporada especificada no existe"
    GPS_INVALIDO = "Las coordenadas GPS deben enviarse juntas"
    ORG_ID_MISSING = "Debe especificar la organización en el header X-Org-Id"
    ORG_ID_UNAUTHORIZED = "No tiene acceso a la organización especificada"
    LOTE_NOT_FOUND = "Lote no encontrado"
    LOTE_NO_EDITABLE = "Solo se pueden editar lotes en estado borrador"
    LOTE_TIENE_MUESTRAS = "No se puede modificar el volumen porque hay muestras asociadas"
    LOTE_DELETE_HAS_MUESTRAS = "No se puede eliminar porque tiene muestras asociadas"
    MUESTRA_NOT_FOUND = "Muestra no encontrada"
    ANALISIS_YA_EXISTE = "Ya existe un análisis para esta muestra"
    ANALISIS_NOT_FOUND = "Análisis no encontrado"
    FICHA_NOT_FOUND = "Ficha no encontrada"
    FICHA_MUESTRA_NO_TOMADA = "No hay una muestra tomada para este lote"
    FICHA_ANALISIS_NO_COMPLETO = "No hay un análisis completo para este lote"
    FICHA_ESTADO_NO_VALIDO = "El lote no está en un estado que permita generar una ficha"
    FICHA_SIN_EVIDENCIAS = "El lote no tiene evidencias fotográficas. Agregá al menos una foto."
    FICHA_SIN_VARIEDAD = "El lote no tiene variedad asignada"
    FICHA_SIN_SUBVARIEDAD = "El lote no tiene subvariedad asignada"

    # Evidencias
    EVIDENCIA_NOT_FOUND = "Evidencia no encontrada"
    TIPO_INVALIDO = "Tipo de evidencia inválido. Debe ser 'foto' o 'video'"
    CONTENT_TYPE_INVALIDO = "Tipo de contenido no permitido"

    # Documentos
    DOCUMENTO_NOT_FOUND = "Documento no encontrado"
    TAMANO_EXCEDIDO = "El archivo excede el tamaño máximo permitido de 20 MB"

    # IA / OCR
    IA_NO_SE_PUDO_PROCESAR = "No se pudo procesar la imagen. Intentá con una foto más clara."
    IA_ARCHIVO_INVALIDO = "El archivo debe ser una imagen válida (JPG, PNG, WEBP)"


class SuccessMessages:
    """Success messages shown to users"""

    LOGOUT_SUCCESS = "Successfully logged out"
    PASSWORD_RESET_SENT = "Password reset email sent"
    LOTE_DELETED = "Lote eliminado correctamente"


class LogMessages:
    """Internal log messages"""

    USER_CREATED = "User created: {user_id}"
    USER_LOGGED_IN = "User logged in: {user_id}"
    USER_LOGGED_OUT = "User logged out successfully"

    # Settings loading
    LOADING_FROM_ENV = "Loading settings from environment variables (GSM disabled)"
    LOADING_FROM_GSM = "Loading secrets from Google Secret Manager"
    GSM_ERROR_FALLBACK = "Error loading secrets from GSM: {error}"
    GSM_FALLBACK_WARNING = "Falling back to environment variables"

    # Secret management
    FETCHING_SECRET_GSM = "Fetching {secret_name} from GSM"
    SECRET_RETRIEVED_GSM = "Successfully retrieved secret {secret_name} from GSM"
    SECRET_LOADED_GSM = "Loaded {secret_name} from Google Secret Manager"
    SECRET_EMPTY_WARNING = "Could not load {secret_name} from GSM, value was empty"
    SECRET_ACCESS_ERROR = "Error accessing secret {secret_name}: {error}"

    # JWT validation
    JWT_MISSING_SUB = "Token is valid but missing 'sub' claim"
    JWT_VALIDATION_FAILED = "JWT validation failed: {error}"
