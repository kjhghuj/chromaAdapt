
import React from 'react';
import { useChromaApp } from './hooks/useChromaApp';
import Header from './components/Header';
import ControlPanel from './components/ControlPanel';
import PreviewPanel from './components/PreviewPanel';

function App() {
  const {
    state,
    isExporting,
    setMode,
    handleFileUpload,
    handleRemoveImage,
    handleGenerate,
    handleAnalyzeSecondary,
    handleAnalyzeEdit,
    handleExport,
    handleStyleChange,
    resetApp,
    toggleLanguage,
    setTranslationTarget,
    setTargetFont,
    onEditPromptChange,
    onEditUserInputChange,
    handlePipelineBatchUpload,
    handleRemovePipelineItem,
    handleBatchTranslateStart,
    setConcurrentCount,
    handleSelectResult,
    togglePrecisionMode,
    handleSecondaryBatchUpload,
    handleRemoveSecondaryBatchItem,
    handleClearSecondaryBatch,
    handleSecondaryBatchGenerate
  } = useChromaApp();

  return (
    <div className="h-screen bg-slate-50 flex flex-col font-sans text-slate-900 overflow-hidden">

      <Header
        language={state.language}
        currentMode={state.mode}
        onModeChange={setMode}
        onToggleLanguage={toggleLanguage}
        onReset={resetApp}
      />

      <main className="flex-1 min-h-0 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">

        {/* Error Notification */}
        {state.errorMessage && (
          <div className="absolute top-20 left-1/2 -translate-x-1/2 z-50 bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg flex items-center gap-3 shadow-lg">
            <div className="w-2 h-2 rounded-full bg-red-500"></div>
            {state.errorMessage}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full">

          <ControlPanel
            state={state}
            onFileUpload={handleFileUpload}
            onRemoveImage={handleRemoveImage}
            onStyleChange={handleStyleChange}
            onTranslationTargetChange={setTranslationTarget}
            onGenerate={handleGenerate}
            onAnalyzeSecondary={handleAnalyzeSecondary}
            onAnalyzeEdit={handleAnalyzeEdit}
            onTargetFontChange={setTargetFont}
            onEditPromptChange={onEditPromptChange}
            onEditUserInputChange={onEditUserInputChange}
            onPipelineBatchUpload={handlePipelineBatchUpload}
            onBatchTranslateStart={handleBatchTranslateStart}
            onConcurrentCountChange={setConcurrentCount}
            onTogglePrecisionMode={togglePrecisionMode}
            onSecondaryBatchUpload={handleSecondaryBatchUpload}
            onSecondaryBatchGenerate={handleSecondaryBatchGenerate}
            onRemoveSecondaryBatchItem={handleRemoveSecondaryBatchItem}
            onClearSecondaryBatch={handleClearSecondaryBatch}
          />

          <PreviewPanel
            state={state}
            onExport={handleExport}
            isExporting={isExporting}
            onRemoveItem={handleRemovePipelineItem}
            onSelectResult={handleSelectResult}
            onRemoveSecondaryBatchItem={handleRemoveSecondaryBatchItem}
          />

        </div>
      </main>
    </div>
  );
}

export default App;
