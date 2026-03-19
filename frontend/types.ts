
export type Language = 'en' | 'zh';

export type AppMode =
  | 'COLOR_ADAPT'
  | 'PRODUCT_REPLACE'
  | 'IMAGE_EDIT'
  | 'TRANSLATION'
  | 'SECONDARY_GENERATION';

export type TranslationTarget = 'zh' | 'en' | 'ja' | 'ko' | 'fr' | 'de' | 'es' | 'ms' | 'tl' | 'th';

export type TargetFont = 'original' | 'sans_serif' | 'serif' | 'handwritten' | 'bold_display';

export type AnalysisModel = 'doubao-seed-2-0-lite' | 'doubao-vision';
export type GenerationModel = 'doubao-seedream-5.0-lite' | 'doubao-seedream-4.0';

export interface ColorPalette {
  main: string;
  secondary: string;
  accent: string;
  mood?: string;
}

export enum ProcessingState {
  IDLE = 'IDLE',
  ANALYZING = 'ANALYZING',
  READY = 'READY',
  GENERATING = 'GENERATING',
  COMPLETE = 'COMPLETE',
  ERROR = 'ERROR'
}

export type PipelineStatus = 'PENDING' | 'TRANSLATING' | 'DONE' | 'ERROR';

export type SecondaryBatchStatus = 'PENDING' | 'PLANNING' | 'PLANNED' | 'GENERATING' | 'DONE' | 'ERROR';

export interface SecondaryBatchItem {
  id: string;
  original: string;
  status: SecondaryBatchStatus;
  plan?: string;
  result?: string;
  error?: string;
}

export interface PipelineItem {
  id: string;
  original: string;
  status: PipelineStatus;
  adapted?: string;
  final?: string;
  error?: string;
}

export interface GenerationProgress {
  completed: number;
  total: number;
  errors: number;
}

export interface AppState {
  mode: AppMode;
  language: Language;
  posterImage: string | null;
  referenceImage: string | null;
  extractedPalette: ColorPalette | null;
  status: ProcessingState;
  errorMessage: string | null;
  resultImage: string | null;
  styleConfig: StyleConfig;
  translationTarget: TranslationTarget;
  targetFont: TargetFont;
  editPrompt: string;
  editUserInput: string;
  // Progress UI
  progress: number;
  progressText: string;
  // Pipeline State
  pipelineQueue: PipelineItem[];
  // Models
  analysisModel: AnalysisModel;
  generationModel: GenerationModel;
  // Concurrent Generation
  concurrentCount: number;
  resultImages: string[];
  generationProgress: GenerationProgress;
  // Precision Mode
  precisionMode: boolean;
  // Secondary Batch
  secondaryBatchQueue: SecondaryBatchItem[];
}

export interface StyleConfig {
  replaceProduct: boolean;
  keepLayout: boolean;
  keepFonts: boolean;
  keepTexture: boolean;
  keepLighting: boolean;
  recolorTextOnly: boolean;
}

export const MOCK_PALETTES: Record<string, ColorPalette> = {
  default: { main: '#3B82F6', secondary: '#93C5FD', accent: '#1E40AF', mood: 'Trustworthy & Calm' },
  tech: { main: '#0F172A', secondary: '#334155', accent: '#38BDF8', mood: 'Modern & Sleek' },
  warm: { main: '#B45309', secondary: '#FCD34D', accent: '#78350F', mood: 'Energetic & Warm' },
};