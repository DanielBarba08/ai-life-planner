def test_cors_header_present_for_browser_origin(client):
    """
    Encontrado al construir el frontend web (Módulo 5): sin CORSMiddleware,
    el navegador bloquea toda llamada del frontend al backend aunque la
    petición en sí sea válida. Esta prueba documenta que el header sigue
    presente — si alguien quita el middleware sin querer, esto falla.
    """
    resp = client.get("/health", headers={"Origin": "http://localhost:8081"})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"
