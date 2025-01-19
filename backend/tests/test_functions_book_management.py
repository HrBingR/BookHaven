from uuid import UUID
from functions.book_management import generate_session_id

def is_valid_uuid(val):
    try:
        return str(UUID(str(val))) == str(val)
    except ValueError:
        return False

def test_generate_sesion_id():
    uuid = generate_session_id()

    assert is_valid_uuid(uuid) is True

