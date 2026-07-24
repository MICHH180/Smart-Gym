export type Exercise = {
  id: string;
  name: string;
  shortDescription: string;
  description: string;
  muscles: string[];
  difficulty: "Principiante" | "Intermedio" | "Avanzado";
  tips: string[];
  available: boolean;
};

export const exercises: Exercise[] = [
  {
    id: "sentadillas",
    name: "Sentadillas",
    shortDescription: "Fuerza de piernas y control de cadera.",
    description:
      "La sentadilla es el ejercicio base para tren inferior: baja controlando la cadera hacia atrás y abajo, manteniendo el torso erguido, hasta que el muslo quede paralelo al piso.",
    muscles: ["Cuádriceps", "Glúteos", "Core"],
    difficulty: "Principiante",
    tips: [
      "Separá los pies al ancho de los hombros.",
      "Bajá empujando la cadera hacia atrás, como si te sentaras.",
      "Mantené el pecho arriba y la espalda neutra.",
      "Las rodillas siguen la dirección de los pies, sin colapsar hacia adentro.",
    ],
    available: true,
  },
  {
    id: "desplantes",
    name: "Desplantes",
    shortDescription: "Estabilidad unilateral y fuerza de piernas.",
    description:
      "El desplante (o zancada) trabaja cada pierna por separado: das un paso adelante y bajás hasta que ambas rodillas queden cerca de 90°, cuidando que la rodilla delantera no pase la punta del pie.",
    muscles: ["Cuádriceps", "Glúteos", "Isquiotibiales"],
    difficulty: "Intermedio",
    tips: [
      "Dá un paso largo hacia adelante antes de bajar.",
      "Bajá en línea recta, sin que la rodilla se vaya hacia adentro.",
      "Mantené el torso vertical durante todo el movimiento.",
      "Alterná de pierna entre repeticiones para trabajar ambos lados.",
    ],
    available: true,
  },
  {
    id: "flexiones",
    name: "Flexiones",
    shortDescription: "Empuje de tren superior y core.",
    description:
      "Próximamente vas a poder practicar flexiones de brazos con corrección de forma en tiempo real, igual que con sentadillas y desplantes.",
    muscles: ["Pecho", "Tríceps", "Core"],
    difficulty: "Intermedio",
    tips: [],
    available: false,
  },
  {
    id: "plancha",
    name: "Plancha",
    shortDescription: "Estabilidad de core e isometría.",
    description:
      "Próximamente vas a poder practicar la plancha con seguimiento de alineación de cadera y espalda en tiempo real.",
    muscles: ["Core", "Espalda baja", "Hombros"],
    difficulty: "Principiante",
    tips: [],
    available: false,
  },
];

export function getExerciseById(id: string): Exercise | undefined {
  return exercises.find((exercise) => exercise.id === id);
}
