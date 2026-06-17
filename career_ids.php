<?php
/**
 * Mapeo de códigos de programa Unibagué → IDs oficiales de Reqlut.
 *
 * PENDIENTE: Reqlut entrega esta lista durante la implementación.
 * La puedes descargar desde: Admin > Users > Alumni Base (en el portal Reqlut).
 *
 * Mientras tanto, se usa el program_code de Unibagué como ID temporal.
 * Una vez tengas la lista, llena el array $CAREER_ID_MAP con la forma:
 *   'program_code_unibague' => id_reqlut
 *
 * Ejemplo:
 *   '23' => 103,   // Ingeniería Industrial → ID 103 en Reqlut
 *   '21' => 101,   // Ingeniería Mecánica   → ID 101 en Reqlut
 */

$CAREER_ID_MAP = [
    // '23' => 103,
    // '21' => 101,
    // Agrega aquí los mapeos cuando los recibas de Reqlut
];

/**
 * Retorna el ID de Reqlut para un código de programa de Unibagué.
 * Si aún no hay mapeo oficial, retorna el program_code como fallback.
 */
function resolveReqlutCareerID(string $programCode): int
{
    global $CAREER_ID_MAP;
    return isset($CAREER_ID_MAP[$programCode])
        ? $CAREER_ID_MAP[$programCode]
        : (int)$programCode;
}
