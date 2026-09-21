<?php
declare(strict_types=1);

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/career_ids.php';

// ── Headers ──────────────────────────────────────────────────────────────────
header('Content-Type: application/json; charset=utf-8');
applyCorsHeaders();

// ── Autenticación (API key) ───────────────────────────────────────────────────
requireApiKey();

// ── Parámetro de búsqueda ─────────────────────────────────────────────────────
$identification = trim($_GET['identification'] ?? '');
$email          = strtolower(trim($_GET['email'] ?? ''));

if ($identification === '' && $email === '') {
    http_response_code(400);
    echo json_encode([
        'error' => 'Se requiere el parámetro "identification" o "email"',
    ]);
    exit;
}

// ── Cargar estudiantes (caché local) ──────────────────────────────────────────
$students = loadStudents();

// ── Filtrar coincidencias ─────────────────────────────────────────────────────
$matches = array_values(array_filter($students, static function (array $s) use ($identification, $email): bool {
    if ($identification !== '' && ($s['identification'] ?? '') === $identification) {
        return true;
    }
    if ($email !== '' && strtolower($s['email'] ?? '') === $email) {
        return true;
    }
    return false;
}));

if (empty($matches)) {
    http_response_code(404);
    exit;
}

// ── Construir respuesta Reqlut ────────────────────────────────────────────────
echo json_encode(buildReqlutResponse($matches), JSON_UNESCAPED_UNICODE);
exit;


// ═════════════════════════════════════════════════════════════════════════════
// Funciones
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Descarga todos los estudiantes desde la API de Unibagué.
 * Usa caché en disco para no superar el tiempo de respuesta de 3 s.
 */
function loadStudents(): array
{
    if (!is_dir(CACHE_DIR)) {
        mkdir(CACHE_DIR, 0755, true);
    }

    $cacheFile = CACHE_DIR . '/students.json';

    // Devolver caché si aún es válida
    if (is_file($cacheFile) && (time() - filemtime($cacheFile)) < CACHE_TTL) {
        $cached = file_get_contents($cacheFile);
        if ($cached !== false) {
            return json_decode($cached, true) ?? [];
        }
    }

    // Descargar desde la API
    $context = stream_context_create([
        'ssl'  => ['verify_peer' => false, 'verify_peer_name' => false],
        'http' => ['timeout' => 20],
    ]);

    $url  = UNIBAGUE_API_URL . '?api_token=' . UNIBAGUE_API_TOKEN;
    $data = @file_get_contents($url, false, $context);

    if ($data === false) {
        // Si falla pero hay caché vieja, úsarla como respaldo
        if (is_file($cacheFile)) {
            $cached = file_get_contents($cacheFile);
            if ($cached !== false) {
                return json_decode($cached, true) ?? [];
            }
        }
        http_response_code(503);
        echo json_encode(['error' => 'No se pudo conectar al servicio de estudiantes de Unibagué']);
        exit;
    }

    $students = json_decode($data, true);
    if (!is_array($students)) {
        http_response_code(503);
        echo json_encode(['error' => 'Respuesta inválida del servicio de estudiantes']);
        exit;
    }

    file_put_contents($cacheFile, $data, LOCK_EX);
    return $students;
}

/**
 * Transforma los registros de Unibagué al formato esperado por Reqlut.
 * Un estudiante puede tener varios programas → múltiples careers.
 */
function buildReqlutResponse(array $records): array
{
    $first = $records[0];

    [$name, $lastName] = parseName($first['name'] ?? '');

    $gender = match (strtoupper($first['sexo'] ?? '')) {
        'F'     => 0,
        'M'     => 1,
        default => 4,
    };

    $careers = array_map('buildCareer', $records);

    return [
        'identification' => $first['identification'] ?? null,
        'email'          => $first['email']          ?? null,
        'email2'         => null,
        'name'           => $name,
        'lastName'       => $lastName,
        'phone'          => null,
        'cellphone'      => normalizePhone($first['telephone'] ?? ''),
        'gender'         => $gender,
        'birthDate'      => null,
        'careers'        => $careers,
    ];
}

/**
 * Construye una entrada de carrera a partir de un registro Unibagué.
 */
function buildCareer(array $record): array
{
    $formation   = (int)($record['formation']    ?? 4);
    $programName = $record['program']            ?? '';
    $status      = $record['status']             ?? '';
    $code        = $record['code_student']       ?? '';
    $programCode = (int)($record['program_code'] ?? 0);

    $type   = resolveCareerType($formation, $programName);
    $state  = resolveCareerState($status);
    $active = in_array($status, ['Activo', 'Inscrito'], true);

    // El año de inicio se codifica en el código de estudiante: PPAAAANNNN
    $initialYear = null;
    if (strlen($code) >= 6) {
        $y = (int)substr($code, 2, 4);
        if ($y >= 1980 && $y <= 2100) {
            $initialYear = $y;
        }
    }

    $career = [
        'type'        => $type,
        'state'       => $state,
        'active'      => $active,
        'internship'  => false,
        'initialYear' => $initialYear,
    ];

    // Para tipos 1 y 10, Reqlut exige el campo id (código numérico del programa)
    if ($type === 1 || $type === 10) {
        $career['id'] = resolveReqlutCareerID((string)$programCode);
    } else {
        $career['programName'] = $programName;
    }

    return $career;
}

/**
 * Determina el tipo de carrera Reqlut usando la formación y el nombre del programa.
 *
 * Tabla Unibagué → Reqlut:
 *   formation 4 = Pregrado              → type 1  (Undergraduate)
 *   formation 5 = Doctorado             → type 10 (Postgraduate Program, requiere id)
 *              = Ciclo Coterminal       → type 10 (Postgraduate Program, requiere id)
 *              = Especialización       → type 10 (Postgraduate Program, requiere id)
 *              = Cursos Libres Posgrado → type 2  (Course)
 *   formation 6 = Maestría              → type 10 (Postgraduate Program, requiere id)
 *
 * Los 42 programas de posgrado del catálogo Reqlut están declarados como
 * type 10; su enlace depende de enviar también el program_code (ver buildCareer).
 */
function resolveCareerType(int $formation, string $program): int
{
    $p = strtoupper($program);

    if ($formation === 6 || str_contains($p, 'MAESTRIA') || str_contains($p, 'MAESTRÍA')) {
        return 10; // Postgraduate Program (Master's)
    }

    if ($formation === 4) {
        return 1; // Undergraduate
    }

    // formation 5 — distinguir por nombre
    if (str_contains($p, 'CURSOS LIBRES') || str_contains($p, 'DIPLOMADO')) {
        return 2; // Course
    }
    if (str_contains($p, 'DOCTORADO')) {
        return 10; // Postgraduate Program (Doctorate)
    }
    if (str_contains($p, 'CICLO COTERMINAL')) {
        return 10; // Postgraduate Program (Ciclo Coterminal)
    }
    if (str_contains($p, 'ESPECIALIZACION') || str_contains($p, 'ESPECIALIZACIÓN') || str_contains($p, 'ESP.')) {
        return 10; // Postgraduate Program (Especialización)
    }

    return 7; // Other
}

/**
 * Mapea el estado académico de Unibagué al código de estado de Reqlut.
 *   0 = Estudiante activo  (Activo, Inscrito — o retirados con active=false)
 *   1 = Titulado           (recibió su diploma formal)
 *   2 = Egresado           (terminó materias, aún sin título)
 */
function resolveCareerState(string $status): int
{
    return match ($status) {
        'Graduado'             => 1,  // Titulado: tiene diploma
        'Egresado'             => 2,  // Egresado: terminó materias, sin título
        'Activo', 'Inscrito'   => 0,
        default                => 0,  // Retirados: activo=false se maneja aparte
    };
}

/**
 * Divide el nombre completo colombiano (APELLIDO1 APELLIDO2 NOMBRE1 NOMBRE2)
 * en nombre y apellido. Devuelve [$name, $lastName] en Title Case.
 */
function parseName(string $fullName): array
{
    $parts = preg_split('/\s+/', trim($fullName));
    $n     = count($parts);

    if ($n >= 4) {
        $lastName = implode(' ', array_slice($parts, 0, 2));
        $name     = implode(' ', array_slice($parts, 2));
    } elseif ($n === 3) {
        $lastName = implode(' ', array_slice($parts, 0, 2));
        $name     = $parts[2];
    } elseif ($n === 2) {
        $lastName = $parts[0];
        $name     = $parts[1];
    } else {
        $lastName = $fullName;
        $name     = '';
    }

    return [
        mb_convert_case($name,     MB_CASE_TITLE, 'UTF-8'),
        mb_convert_case($lastName, MB_CASE_TITLE, 'UTF-8'),
    ];
}

/**
 * Devuelve null para teléfonos vacíos o con solo ceros.
 */
function normalizePhone(string $phone): ?string
{
    $phone = trim($phone);
    return ($phone === '' || $phone === '0') ? null : $phone;
}

/**
 * Envía el header CORS según REQLUT_ALLOWED_ORIGINS.
 * "*" permite cualquier origen; una lista separada por comas solo
 * habilita el origen exacto que envíe el cliente (con Vary: Origin).
 */
function applyCorsHeaders(): void
{
    if (REQLUT_ALLOWED_ORIGINS === '*') {
        header('Access-Control-Allow-Origin: *');
        return;
    }

    $allowed = array_map('trim', explode(',', REQLUT_ALLOWED_ORIGINS));
    $origin  = $_SERVER['HTTP_ORIGIN'] ?? '';

    if ($origin !== '' && in_array($origin, $allowed, true)) {
        header('Access-Control-Allow-Origin: ' . $origin);
        header('Vary: Origin');
    }
    // Si el origen no está en la lista (o no viene, p. ej. llamadas
    // servidor-a-servidor), simplemente no se envía el header CORS.
}

/**
 * Exige una API key válida en el header "X-Api-Key" o el parámetro
 * "api_key" cuando WEBSERVICE_API_KEY está configurada. Si no está
 * configurada, el endpoint queda abierto (compatibilidad hacia atrás).
 */
function requireApiKey(): void
{
    if (WEBSERVICE_API_KEY === '') {
        return;
    }

    $provided = $_SERVER['HTTP_X_API_KEY'] ?? ($_GET['api_key'] ?? '');

    if (!hash_equals(WEBSERVICE_API_KEY, (string)$provided)) {
        http_response_code(401);
        echo json_encode(['error' => 'API key inválida o ausente']);
        exit;
    }
}
