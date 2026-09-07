import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AcademicYear, ClassGroup, Level, ScopeType, Stream, Subject } from "../types";

export interface ScopeOption {
  id: string;
  name: string;
}

export type ScopeOptionsMap = Partial<Record<ScopeType, ScopeOption[]>>;

/**
 * Charge les listes nommées (campus, niveaux, séries, classes, matières, périodes)
 * nécessaires pour construire des sélecteurs lisibles dans la matrice de permissions,
 * plutôt que de demander à l'administrateur de saisir des UUID à la main.
 */
export function useScopeOptions(schoolId: string | undefined) {
  const [options, setOptions] = useState<ScopeOptionsMap>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!schoolId) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const [campusesRes, levelsRes, subjectsRes, yearsRes] = await Promise.all([
          api.get(`/api/schools/${schoolId}/campuses`),
          api.get<Level[]>(`/api/schools/${schoolId}/levels`),
          api.get<Subject[]>(`/api/schools/${schoolId}/subjects`),
          api.get<AcademicYear[]>(`/api/schools/${schoolId}/academic-years`),
        ]);

        const levels: Level[] = levelsRes.data;
        const streamsNested = await Promise.all(levels.map((lvl) => api.get<Stream[]>(`/api/levels/${lvl.id}/streams`)));
        const streams: Stream[] = streamsNested.flatMap((r) => r.data);

        const currentYear = yearsRes.data.find((y: AcademicYear) => y.is_current);
        let classes: ClassGroup[] = [];
        let periods: { id: string; label: string }[] = [];
        if (currentYear) {
          const [classesRes, periodsRes] = await Promise.all([
            api.get<ClassGroup[]>(`/api/academic-years/${currentYear.id}/classes`),
            api.get(`/api/academic-years/${currentYear.id}/periods`),
          ]);
          classes = classesRes.data;
          periods = periodsRes.data;
        }

        if (cancelled) return;

        setOptions({
          campus: campusesRes.data.map((c: any) => ({ id: c.id, name: c.name })),
          level: levels.map((l) => ({ id: l.id, name: l.name })),
          stream: streams.map((s) => ({ id: s.id, name: s.name })),
          class: classes.map((c) => ({ id: c.id, name: c.name })),
          subject: subjectsRes.data.map((s) => ({ id: s.id, name: `${s.name} (${s.code})` })),
          period: periods.map((p) => ({ id: p.id, name: p.label })),
        });
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [schoolId]);

  return { options, loading };
}
