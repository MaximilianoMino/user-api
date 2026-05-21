import logging
from supabase import Client

logger = logging.getLogger(__name__)


async def crear_perfil_usuario(
    client: Client,
    auth_user_id: str,
    email: str,
    nombre: str
) -> dict:
    """
    Inserta un perfil en public.usuario.
    
    Args:
        client: Cliente de Supabase
        auth_user_id: ID del usuario en Supabase Auth (UUID)
        email: Email del usuario
        nombre: Nombre completo del usuario
    
    Returns:
        dict: Los datos del perfil creado
    
    Raises:
        Exception: Si la inserción falla
    """
    try:
        data = {
            "auth_user_id": auth_user_id,
            "email": email,
            "nombre": nombre,
            "created_by": None,
            "updated_by": None
        }
        
        result = client.table("usuario").insert(data).execute()
        
        if not result.data:
            raise Exception("No se pudo crear el perfil de usuario")
        
        logger.info(f"Perfil de usuario creado: {result.data[0].get('user_id')}")
        return result.data[0]
        
    except Exception as e:
        logger.error(f"Error al crear perfil de usuario: {e}")
        raise


async def obtener_perfil_por_auth_user_id(
    client: Client,
    auth_user_id: str
) -> dict | None:
    """
    Obtiene un perfil de usuario por auth_user_id.
    
    Args:
        client: Cliente de Supabase
        auth_user_id: ID del usuario en Supabase Auth
    
    Returns:
        dict | None: Los datos del perfil o None si no existe
    """
    try:
        result = (
            client.table("usuario")
            .select("*")
            .eq("auth_user_id", auth_user_id)
            .execute()
        )
        
        if result.data:
            return result.data[0]
        return None
        
    except Exception as e:
        logger.error(f"Error al obtener perfil de usuario: {e}")
        return None