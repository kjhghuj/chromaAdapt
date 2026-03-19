
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { AppState, ProcessingState, StyleConfig, AppMode, TranslationTarget, TargetFont, GenerationProgress, SecondaryBatchItem } from '../types';
import { analyzeImageColors, generatePosterAdaptation, generateImageTranslation, generateProductReplacement, generateImageEdit, generateSecondaryImage, generateSecondaryImagePlan, createColorMappingPlan, generatePreciseAdaptation, analyzeAndCreateEditPrompt } from '../services/apiService';
import { getCSSFilterFromPalette, exportImage } from '../utils/imageHelpers';
import { getTranslation } from '../utils/translations';
import { useFileHandlers } from './useFileHandlers';
import { usePipelineLogic } from './usePipelineLogic';

const INITIAL_GENERATION_PROGRESS: GenerationProgress = { completed: 0, total: 0, errors: 0 };

const INITIAL_STYLE_CONFIG: StyleConfig = {
  replaceProduct: true,
  keepLayout: true,
  keepFonts: true,
  keepTexture: true,
  keepLighting: true,
  recolorTextOnly: false,
};

export const useChromaApp = () => {
  const [state, setState] = useState<AppState>({
    mode: 'COLOR_ADAPT',
    language: 'zh',
    posterImage: null,
    referenceImage: null,
    extractedPalette: null,
    status: ProcessingState.IDLE,
    errorMessage: null,
    resultImage: null,
    styleConfig: INITIAL_STYLE_CONFIG,
    translationTarget: 'en',
    targetFont: 'original',
    editPrompt: '',
    editUserInput: '',
    progress: 0,
    progressText: '',
    pipelineQueue: [],
    analysisModel: 'doubao-seed-2-0-lite',
    generationModel: 'doubao-seedream-5.0-lite',
    concurrentCount: 1,
    resultImages: [],
    generationProgress: { ...INITIAL_GENERATION_PROGRESS },
    precisionMode: false,
    secondaryBatchQueue: []
  });

  const [isExporting, setIsExporting] = useState(false);
  const progressInterval = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (progressInterval.current) window.clearInterval(progressInterval.current);
    };
  }, []);

  const performAnalysis = useCallback(async (imageData: string) => {
    setState(prev => ({ ...prev, status: ProcessingState.ANALYZING }));
    try {
      const palette = await analyzeImageColors(imageData, state.language, state.analysisModel);
      setState(prev => ({
        ...prev,
        extractedPalette: palette,
        status: prev.posterImage ? ProcessingState.READY : ProcessingState.IDLE
      }));
      return palette;
    } catch (error) {
      console.error("Analysis failed", error);
      setState(prev => ({
        ...prev,
        status: ProcessingState.ERROR,
        errorMessage: '色彩分析失败'
      }));
      return null;
    }
  }, [state.language, state.analysisModel]);

  const {
    handleFileUpload,
    handlePipelineRefUpload,
    handlePipelineBatchUpload
  } = useFileHandlers({
    state,
    setState,
    performAnalysis
  });

  const {
    handleBatchTranslateStart,
    handleRemovePipelineItem
  } = usePipelineLogic({ state, setState });

  const setMode = useCallback((newMode: AppMode) => {
    setState(prev => ({
      ...prev,
      mode: newMode,
      status: prev.status === ProcessingState.GENERATING ? ProcessingState.GENERATING : (prev.posterImage ? ProcessingState.READY : ProcessingState.IDLE),
      errorMessage: null,
      resultImage: null,
      editPrompt: '',
      editUserInput: ''
    }));
  }, []);

  const handleRemoveImage = useCallback((type: 'poster' | 'reference', e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    setState(prev => ({
      ...prev,
      [type === 'poster' ? 'posterImage' : 'referenceImage']: null,
      extractedPalette: type === 'reference' ? null : prev.extractedPalette,
      resultImage: type === 'poster' ? null : prev.resultImage,
      resultImages: type === 'poster' ? [] : prev.resultImages,
      status: ProcessingState.IDLE,
      progress: 0,
      editPrompt: '',
      generationProgress: { ...INITIAL_GENERATION_PROGRESS }
    }));
  }, []);

  const resetApp = useCallback(() => {
    setState(prev => ({
      ...prev,
      posterImage: null,
      referenceImage: null,
      extractedPalette: null,
      status: ProcessingState.IDLE,
      errorMessage: null,
      resultImage: null,
      resultImages: [],
      secondaryBatchQueue: [],
      styleConfig: INITIAL_STYLE_CONFIG,
      editPrompt: '',
      editUserInput: '',
      progress: 0,
      progressText: '',
      pipelineQueue: [],
      analysisModel: 'doubao-seed-2-0-lite',
      generationModel: 'doubao-seedream-5.0-lite',
      generationProgress: { ...INITIAL_GENERATION_PROGRESS },
      precisionMode: false
    }));
    if (progressInterval.current) clearInterval(progressInterval.current);
  }, []);

  const toggleLanguage = useCallback(() => {
    setState(prev => ({
      ...prev,
      language: prev.language === 'en' ? 'zh' : 'en'
    }));
  }, []);

  const setTranslationTarget = useCallback((target: TranslationTarget) => {
    setState(prev => ({ ...prev, translationTarget: target, editPrompt: '' }));
  }, []);

  const setTargetFont = useCallback((font: TargetFont) => {
    setState(prev => ({ ...prev, targetFont: font, editPrompt: '' }));
  }, []);

  const setEditPrompt = useCallback((val: string) => {
    setState(prev => ({ ...prev, editPrompt: val }));
  }, []);

  const setEditUserInput = useCallback((val: string) => {
    setState(prev => ({ ...prev, editUserInput: val }));
  }, []);

  const setAnalysisModel = useCallback((modelKey: any) => {
    setState(prev => ({ ...prev, analysisModel: modelKey }));
  }, []);

  const setGenerationModel = useCallback((modelKey: any) => {
    setState(prev => ({ ...prev, generationModel: modelKey }));
  }, []);

  const setConcurrentCount = useCallback((count: number) => {
    const clamped = Math.max(1, Math.min(4, count));
    setState(prev => ({ ...prev, concurrentCount: clamped }));
  }, []);

  const handleSelectResult = useCallback((index: number) => {
    setState(prev => {
      if (index < 0 || index >= prev.resultImages.length) return prev;
      return { ...prev, resultImage: prev.resultImages[index] };
    });
  }, []);

  const togglePrecisionMode = useCallback(() => {
    setState(prev => ({ ...prev, precisionMode: !prev.precisionMode }));
  }, []);

  const handleStyleChange = useCallback((key: keyof StyleConfig) => {
    setState(prev => ({
      ...prev,
      styleConfig: {
        ...prev.styleConfig,
        [key]: !prev.styleConfig[key]
      }
    }));
  }, []);

  const handleAnalyzeSecondary = useCallback(async () => {
    if (!state.posterImage) return;

    setState(prev => ({ ...prev, status: ProcessingState.ANALYZING, progressText: 'AI Creating Plan...' }));

    try {
      const plan = await generateSecondaryImagePlan(state.posterImage, state.analysisModel);
      setState(prev => ({
        ...prev,
        status: ProcessingState.READY,
        editPrompt: plan
      }));
    } catch (e: any) {
      console.error("Secondary Plan Generation Failed", e);
      setState(prev => ({ ...prev, status: ProcessingState.ERROR, errorMessage: "Failed to generate plan." }));
    }
  }, [state.posterImage, state.analysisModel]);

  // ── Image Edit Deep Analysis ──

  const handleAnalyzeEdit = useCallback(async () => {
    if (!state.posterImage || !state.editUserInput) return;

    setState(prev => ({ ...prev, status: ProcessingState.ANALYZING, progressText: 'AI Deep Analyzing...' }));

    try {
      const professionalPrompt = await analyzeAndCreateEditPrompt(
        state.posterImage,
        state.editUserInput,
        state.referenceImage,
        state.analysisModel
      );
      setState(prev => ({
        ...prev,
        status: ProcessingState.READY,
        editPrompt: professionalPrompt
      }));
    } catch (e: any) {
      console.error("Edit Analysis Failed", e);
      setState(prev => ({ ...prev, status: ProcessingState.ERROR, errorMessage: "Failed to analyze edit request." }));
    }
  }, [state.posterImage, state.editUserInput, state.referenceImage, state.analysisModel]);

  const startSimulatedProgress = () => {
    setState(prev => ({ ...prev, progress: 5, progressText: 'Initialization...' }));
    if (progressInterval.current) clearInterval(progressInterval.current);

    progressInterval.current = window.setInterval(() => {
      setState(prev => {
        if (prev.status !== ProcessingState.GENERATING) return prev;
        const increment = prev.progress < 50 ? 5 : (prev.progress < 80 ? 2 : 0.5);
        const newProgress = Math.min(prev.progress + increment, 90);

        let text = 'Processing...';
        if (state.mode === 'SECONDARY_GENERATION') {
          if (newProgress < 50) text = 'Composing 1:1 format...';
          else text = 'Rendering detail shot...';
        } else if (state.mode === 'TRANSLATION') {
          if (newProgress < 50) text = 'Translating content...';
          else text = 'Reconstructing layout...';
        } else {
          if (newProgress < 30) text = 'Analyzing composition...';
          else if (newProgress < 60) text = 'Applying neural adaptation...';
          else if (newProgress < 85) text = 'Refining details...';
          else text = 'Finalizing output...';
        }

        return { ...prev, progress: newProgress, progressText: text };
      });
    }, 500);
  };

  // ── Secondary Batch Handlers ──

  const handleSecondaryBatchUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const fileArray = Array.from(files) as File[];
    fileArray.forEach(file => {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (typeof event.target?.result === 'string') {
          const newItem: SecondaryBatchItem = {
            id: Math.random().toString(36).substr(2, 9),
            original: event.target.result as string,
            status: 'PENDING'
          };
          setState(prev => ({
            ...prev,
            secondaryBatchQueue: [...prev.secondaryBatchQueue, newItem]
          }));
        }
      };
      reader.readAsDataURL(file);
    });
    e.target.value = '';
  }, [setState]);

  const handleRemoveSecondaryBatchItem = useCallback((id: string) => {
    setState(prev => ({
      ...prev,
      secondaryBatchQueue: prev.secondaryBatchQueue.filter(item => item.id !== id)
    }));
  }, [setState]);

  const handleClearSecondaryBatch = useCallback(() => {
    setState(prev => ({
      ...prev,
      secondaryBatchQueue: [],
      generationProgress: { ...INITIAL_GENERATION_PROGRESS }
    }));
  }, [setState]);

  const handleSecondaryBatchGenerate = useCallback(async () => {
    const queue = state.secondaryBatchQueue;
    if (queue.length === 0) return;

    if ((window as any).aistudio) {
      try {
        const hasKey = await (window as any).aistudio.hasSelectedApiKey();
        if (!hasKey) await (window as any).aistudio.openSelectKey();
      } catch (e) { console.error(e); }
    }

    const total = queue.length;
    setState(prev => ({
      ...prev,
      status: ProcessingState.GENERATING,
      errorMessage: null,
      generationProgress: { completed: 0, total, errors: 0 }
    }));

    const updateItem = (id: string, updates: Partial<SecondaryBatchItem>) => {
      setState(prev => ({
        ...prev,
        secondaryBatchQueue: prev.secondaryBatchQueue.map(item =>
          item.id === id ? { ...item, ...updates } : item
        )
      }));
    };

    const promises = queue.map(async (item) => {
      try {
        // Step 1: Plan
        updateItem(item.id, { status: 'PLANNING' });
        const plan = await generateSecondaryImagePlan(item.original, state.analysisModel);
        updateItem(item.id, { status: 'PLANNED', plan });

        // Step 2: Generate
        updateItem(item.id, { status: 'GENERATING' });
        const result = await generateSecondaryImage(item.original, plan, state.generationModel);
        updateItem(item.id, { status: 'DONE', result });

        setState(prev => ({
          ...prev,
          generationProgress: {
            ...prev.generationProgress,
            completed: prev.generationProgress.completed + 1
          }
        }));
        return result;
      } catch (error: any) {
        console.error(`Batch item ${item.id} failed:`, error);
        updateItem(item.id, { status: 'ERROR', error: error.message || 'Generation failed' });
        setState(prev => ({
          ...prev,
          generationProgress: {
            ...prev.generationProgress,
            completed: prev.generationProgress.completed + 1,
            errors: prev.generationProgress.errors + 1
          }
        }));
        throw error;
      }
    });

    const results = await Promise.allSettled(promises);
    const errorCount = results.filter(r => r.status === 'rejected').length;
    const successCount = results.filter(r => r.status === 'fulfilled').length;

    setState(prev => ({
      ...prev,
      status: ProcessingState.COMPLETE,
      generationProgress: { completed: total, total, errors: errorCount },
      errorMessage: errorCount > 0
        ? (prev.language === 'zh' ? `${errorCount} 张生成失败` : `${errorCount} generation(s) failed`)
        : null
    }));
  }, [state.secondaryBatchQueue, state.analysisModel, state.generationModel]);

  const handleGenerate = useCallback(async () => {
    if (!state.posterImage) return;
    if (state.mode === 'COLOR_ADAPT' || state.mode === 'PRODUCT_REPLACE') {
      if (!state.referenceImage) return;
    }
    if (state.mode === 'SECONDARY_GENERATION' && !state.editPrompt) return;
    if (state.mode === 'IMAGE_EDIT' && !state.editPrompt) return;

    if ((window as any).aistudio) {
      try {
        const hasKey = await (window as any).aistudio.hasSelectedApiKey();
        if (!hasKey) await (window as any).aistudio.openSelectKey();
      } catch (e) { console.error(e); }
    }

    // Concurrent generation for COLOR_ADAPT mode
    const isConcurrent = state.mode === 'COLOR_ADAPT' && state.concurrentCount > 1;

    setState(prev => ({
      ...prev,
      status: ProcessingState.GENERATING,
      errorMessage: null,
      resultImages: [],
      resultImage: null,
      generationProgress: isConcurrent
        ? { completed: 0, total: state.concurrentCount, errors: 0 }
        : { ...INITIAL_GENERATION_PROGRESS }
    }));
    startSimulatedProgress();

    try {
      // --- Precision mode: run color mapping analysis first ---
      let colorMappingPlan: string | null = null;
      if (state.mode === 'COLOR_ADAPT' && state.precisionMode) {
        setState(prev => ({
          ...prev,
          progressText: prev.language === 'zh' ? '正在分析色彩区域...' : 'Analyzing color zones...'
        }));
        colorMappingPlan = await createColorMappingPlan(
          state.posterImage!,
          state.referenceImage!,
          state.analysisModel
        );
        setState(prev => ({
          ...prev,
          progress: 15,
          progressText: prev.language === 'zh' ? '色彩映射完成，开始生成...' : 'Mapping complete, generating...'
        }));
      }

      if (isConcurrent) {
        // --- Concurrent generation path ---
        const count = state.concurrentCount;
        const promises = Array.from({ length: count }, (_, i) =>
          (colorMappingPlan
            ? generatePreciseAdaptation(
              state.posterImage!,
              state.referenceImage!,
              state.extractedPalette!,
              state.styleConfig,
              colorMappingPlan,
              state.generationModel
            )
            : generatePosterAdaptation(
              state.posterImage!,
              state.referenceImage!,
              state.extractedPalette!,
              state.styleConfig,
              state.language,
              state.generationModel
            )
          ).then((result) => {
            // Incrementally update as each image completes
            setState(prev => {
              const newImages = [...prev.resultImages, result];
              const newProgress = {
                completed: prev.generationProgress.completed + 1,
                total: count,
                errors: prev.generationProgress.errors
              };
              const progressPercent = Math.round((newProgress.completed / count) * 90) + 5;
              return {
                ...prev,
                resultImages: newImages,
                resultImage: prev.resultImage || result, // first success becomes primary
                generationProgress: newProgress,
                progress: progressPercent,
                progressText: `${prev.language === 'zh' ? '正在生成' : 'Generating'} ${newProgress.completed}/${count}...`
              };
            });
            return result;
          })
        );

        const results = await Promise.allSettled(promises);
        const errorCount = results.filter(r => r.status === 'rejected').length;
        const successCount = results.filter(r => r.status === 'fulfilled').length;

        if (progressInterval.current) clearInterval(progressInterval.current);

        if (successCount === 0) {
          const firstError = results.find(r => r.status === 'rejected') as PromiseRejectedResult;
          throw new Error(firstError?.reason?.message || 'All generations failed');
        }

        setState(prev => ({
          ...prev,
          status: ProcessingState.COMPLETE,
          progress: 100,
          progressText: prev.language === 'zh' ? '全部完成！' : 'All Complete!',
          generationProgress: { completed: successCount, total: count, errors: errorCount },
          errorMessage: errorCount > 0
            ? (prev.language === 'zh' ? `${errorCount} 张生成失败` : `${errorCount} generation(s) failed`)
            : null
        }));

      } else {
        // --- Single generation path (original logic) ---
        let generatedImage = '';

        if (state.mode === 'COLOR_ADAPT') {
          if (colorMappingPlan) {
            generatedImage = await generatePreciseAdaptation(
              state.posterImage!,
              state.referenceImage!,
              state.extractedPalette!,
              state.styleConfig,
              colorMappingPlan,
              state.generationModel
            );
          } else {
            generatedImage = await generatePosterAdaptation(
              state.posterImage!,
              state.referenceImage!,
              state.extractedPalette!,
              state.styleConfig,
              state.language,
              state.generationModel
            );
          }
        } else if (state.mode === 'PRODUCT_REPLACE') {
          generatedImage = await generateProductReplacement(
            state.posterImage!,
            state.referenceImage!
          );
        } else if (state.mode === 'IMAGE_EDIT') {
          generatedImage = await generateImageEdit(
            state.posterImage!,
            state.editUserInput || state.editPrompt,
            state.referenceImage,
            state.generationModel,
            state.editPrompt || null
          );
        } else if (state.mode === 'SECONDARY_GENERATION') {
          generatedImage = await generateSecondaryImage(
            state.posterImage!,
            state.editPrompt
          );
        } else {
          const translationResult = await generateImageTranslation(
            state.posterImage!,
            state.translationTarget,
            state.targetFont,
            state.generationModel
          );
          generatedImage = translationResult.url;
          // Update the editPrompt with the AI-generated translation instructions for user review
          if (translationResult.instructions) {
            const instr = translationResult.instructions;
            let instructionsText = "【翻译指令详情】\n\n";
            if (instr.translations && instr.translations.length > 0) {
              instructionsText += "文字映射：\n";
              instr.translations.forEach((t: any) => {
                instructionsText += `- "${t.original}" → "${t.translated}"\n`;
              });
              instructionsText += `\n视觉背景：${instr.visual_context || '未提供'}\n`;
            } else if (instr.error) {
              instructionsText += `状态：${instr.error}\n`;
            }
            setState(prev => ({ ...prev, editPrompt: instructionsText }));
          }
        }

        setState(prev => ({
          ...prev,
          status: ProcessingState.COMPLETE,
          resultImage: generatedImage,
          resultImages: [generatedImage],
          progress: 100,
          progressText: prev.language === 'zh' ? '完成！' : 'Completed!'
        }));

        if (progressInterval.current) clearInterval(progressInterval.current);
      }

    } catch (e: any) {
      console.error("Generation failed", e);
      if (progressInterval.current) clearInterval(progressInterval.current);

      let errorMsg = e.message || "Generation failed";
      if (errorMsg.includes("Requested entity was not found") || errorMsg.includes("403")) {
        if ((window as any).aistudio) {
          await (window as any).aistudio.openSelectKey();
        }
        errorMsg = "API Key Error. Please re-select key.";
      }
      setState(prev => ({ ...prev, status: ProcessingState.ERROR, errorMessage: errorMsg, progress: 0 }));
    }
  }, [state.mode, state.posterImage, state.referenceImage, state.extractedPalette, state.styleConfig, state.language, state.translationTarget, state.targetFont, state.editPrompt, state.analysisModel, state.generationModel, state.concurrentCount]);

  const handleExport = useCallback(async () => {
    const isBatchTranslateMode = state.mode === 'TRANSLATION' && state.pipelineQueue.length > 0;
    const isSecondaryBatchMode = state.mode === 'SECONDARY_GENERATION' && state.secondaryBatchQueue.length > 0;

    if (isBatchTranslateMode) {
      if (state.pipelineQueue.length === 0) return;
      setIsExporting(true);
      try {
        for (let i = 0; i < state.pipelineQueue.length; i++) {
          const item = state.pipelineQueue[i];
          const imageToExport = item.final || item.original;
          await exportImage(imageToExport, 'none', `chroma-batch-${i + 1}-${Date.now()}.png`);
          await new Promise(resolve => setTimeout(resolve, 300));
        }
      } catch (error) {
        console.error("Batch export failed", error);
        setState(prev => ({ ...prev, errorMessage: "Batch export failed" }));
      } finally {
        setIsExporting(false);
      }
      return;
    }

    if (isSecondaryBatchMode) {
      const doneItems = state.secondaryBatchQueue.filter(item => item.status === 'DONE' && item.result);
      if (doneItems.length === 0) return;
      setIsExporting(true);
      try {
        for (let i = 0; i < doneItems.length; i++) {
          await exportImage(doneItems[i].result!, 'none', `chroma-secondary-${i + 1}-${Date.now()}.png`);
          await new Promise(resolve => setTimeout(resolve, 300));
        }
      } catch (error) {
        console.error("Secondary batch export failed", error);
        setState(prev => ({ ...prev, errorMessage: "Batch export failed" }));
      } finally {
        setIsExporting(false);
      }
      return;
    }

    if (!state.resultImage) return;
    setIsExporting(true);
    try {
      const filter = state.resultImage === state.posterImage && state.mode === 'COLOR_ADAPT'
        ? getCSSFilterFromPalette(state.extractedPalette)
        : 'none';
      await exportImage(state.resultImage, filter, `chroma-${state.mode.toLowerCase()}-${Date.now()}.png`);
    } catch (error) {
      console.error("Export failed", error);
      setState(prev => ({ ...prev, errorMessage: "Export failed" }));
    } finally {
      setIsExporting(false);
    }
  }, [state.resultImage, state.posterImage, state.mode, state.extractedPalette, state.pipelineQueue, state.secondaryBatchQueue]);

  return {
    state,
    isExporting,
    setMode,
    handleFileUpload,
    handlePipelineBatchUpload,
    handleRemoveImage,
    handleRemovePipelineItem,
    handleGenerate,
    handleAnalyzeSecondary,
    handleBatchTranslateStart,
    handleExport,
    handleStyleChange,
    resetApp,
    toggleLanguage,
    setTranslationTarget,
    setTargetFont,
    onEditPromptChange: setEditPrompt,
    onEditUserInputChange: setEditUserInput,
    handleAnalyzeEdit,
    setAnalysisModel,
    setGenerationModel,
    setConcurrentCount,
    handleSelectResult,
    togglePrecisionMode,
    handleSecondaryBatchUpload,
    handleRemoveSecondaryBatchItem,
    handleClearSecondaryBatch,
    handleSecondaryBatchGenerate
  };
};
