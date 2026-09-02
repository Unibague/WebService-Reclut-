<?php
declare(strict_types=1);

/**
 * Invalida manualmente la caché de estudiantes (cache/students.json).
 * Útil cuando hay un cambio urgente en Unibagué y no se quiere esperar
 * hasta que expire CACHE_TTL.
 *
 * Uso:
 *   GET /clear_cache.php?key=TU_CACHE_ADMIN_KEY
 *
 * Requiere que CACHE_ADMIN_KEY esté configurada en .env; si está vacía,
 * este endpoint rechaza siempre la solicitud.
 */

require_once __DIR__ . '/config.php';

header('Content-Type: application/json; charset=utf-8');

if (CACHE_ADMIN_KEY === '') {
    http_response_code(403);
    echo json_encode(['error' => 'La invalidación de caché está deshabilitada (CACHE_ADMIN_KEY no configurada)']);
    exit;
}

$provided = $_GET['key'] ?? '';

if (!hash_equals(CACHE_ADMIN_KEY, (string)$provided)) {
    http_response_code(401);
    echo json_encode(['error' => 'Clave de administración inválida o ausente']);
    exit;
}

$cacheFile = CACHE_DIR . '/students.json';

if (is_file($cacheFile) && !unlink($cacheFile)) {
    http_response_code(500);
    echo json_encode(['error' => 'No se pudo eliminar el archivo de caché']);
    exit;
}

echo json_encode([
    'success' => true,
    'message' => 'Caché invalidada. La próxima solicitud recargará los datos desde Unibagué.',
]);
