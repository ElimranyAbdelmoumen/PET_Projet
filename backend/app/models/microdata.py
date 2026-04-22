from app.utils.db import fetchall, fetchone


def list_microdata_files():
    return fetchall(
        "SELECT guid, name, description FROM microdata_files ORDER BY name",
        ()
    )


def get_microdata_by_guid(guid):
    return fetchone(
        "SELECT guid, name, file_path FROM microdata_files WHERE guid=%s",
        (guid,)
    )
