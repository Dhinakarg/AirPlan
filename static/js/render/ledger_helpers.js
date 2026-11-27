/**
 * @fileoverview Pure routine sorting, 24-hour gap detection, and coverage helpers.
 */

/**
 * Sort routine blocks chronologically by start_hour then end_hour.
 * @param {Array<{start_hour: number, end_hour: number, activity: string, mode: string}>} routine
 * @returns {Array<{start_hour: number, end_hour: number, activity: string, mode: string}>}
 */
export function sortRoutine(routine) {
  return [...routine].sort((a, b) => (a.start_hour - b.start_hour) || (a.end_hour - b.end_hour));
}

/**
 * Compute total covered hours and find the first uncovered [start, end] gap in 0..24.
 * @param {Array<{start_hour: number, end_hour: number}>} routine
 * @returns {{covered: number, gapStart: number, gapEnd: number}}
 */
export function analyzeRoutineCoverage(routine) {
  const hours = new Array(24).fill(false);
  routine.forEach((b) => {
    for (let h = Math.max(0, b.start_hour); h < Math.min(24, b.end_hour); h += 1) {
      hours[h] = true;
    }
  });
  const covered = hours.filter(Boolean).length;
  const firstGap = hours.indexOf(false);
  if (firstGap === -1) return { covered, gapStart: 12, gapEnd: 14 };
  let end = firstGap + 1;
  while (end < 24 && !hours[end] && end - firstGap < 2) end += 1;
  return { covered, gapStart: firstGap, gapEnd: end };
}

