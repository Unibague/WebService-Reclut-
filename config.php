<?php
declare(strict_types=1);

/**
 * Carga variables desde un archivo .env (formato KEY=VALUE) si existe.
 * No sobrescribe variables que ya estén definidas en el entorno real
 * (permite que Docker/Apache tengan prioridad sobre el archivo .env).
 */
function loadEnvFile(string $path): void
{
    if (!is_file($path)) {
        return;
    }

    foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#')) {
            continue;
        }
        if (!str_contains($line, '=')) {
            continue;
        }
        [$key, $value] = explode('=', $line, 2);
        $key   = trim($key);
        $value = trim($value, " \t\n\r\0\x0B\"'");

        if (getenv($key) === false) {
            putenv("$key=$value");
        }
    }
}

loadEnvFile(__DIR__ . '/.env');

/**
 * Lee una variable de entorno obligatoria. Detiene la ejecución con un
 * error claro si no está configurada (evita que el servicio arranque
 * con credenciales vacías).
 */
function requireEnv(string $key): string
{
    $value = getenv($key);
    if ($value === false || trim($value) === '') {
        http_response_code(500);
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode([
            'error' => "Falta configurar la variable de entorno \"$key\" (ver .env.example)",
        ]);
        exit;
    }
    return $value;
}

function envOr(string $key, string $default): string
{
    $value = getenv($key);
    return ($value === false || $value === '') ? $default : $value;
}

// ── Integración con la API de Unibagué ────────────────────────────────────
define('UNIBAGUE_API_URL',   envOr('UNIBAGUE_API_URL', 'http://integra.unibague.edu.co/students/all'));
define('UNIBAGUE_API_TOKEN', requireEnv('UNIBAGUE_API_TOKEN'));

// ── Caché local ────────────────────────────────────────────────────────────
define('CACHE_DIR', __DIR__ . '/cache');
define('CACHE_TTL', (int)envOr('CACHE_TTL', '3600')); // segundos — recarga cada hora

// ── Seguridad del endpoint ─────────────────────────────────────────────────
// Dominios permitidos para CORS, separados por coma. "*" = sin restricción.
define('REQLUT_ALLOWED_ORIGINS', envOr('REQLUT_ALLOWED_ORIGINS', '*'));

// API key que Reqlut debe enviar (header "X-Api-Key" o parámetro "api_key").
// Si se deja vacía, el endpoint queda abierto (no recomendado en producción).
define('WEBSERVICE_API_KEY', envOr('WEBSERVICE_API_KEY', ''));

// Clave para invalidar la caché manualmente vía clear_cache.php.
// Si se deja vacía, clear_cache.php rechaza todas las solicitudes.
define('CACHE_ADMIN_KEY', envOr('CACHE_ADMIN_KEY', ''));
