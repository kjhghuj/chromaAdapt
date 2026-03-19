
import React from 'react';
import { RefreshCw, Globe, Palette, Languages, Box, ImagePlus, Copy, Workflow } from 'lucide-react';
import { Language, AppMode } from '../types';
import { getTranslation } from '../utils/translations';

interface HeaderProps {
  language: Language;
  currentMode: AppMode;
  onModeChange: (mode: AppMode) => void;
  onToggleLanguage: () => void;
  onReset: () => void;
}

const Header: React.FC<HeaderProps> = ({
  language,
  currentMode,
  onModeChange,
  onToggleLanguage,
  onReset
}) => {
  const t = getTranslation(language);

  const navItems = [
    { id: 'COLOR_ADAPT' as AppMode, icon: Palette, label: t.modeColor },
    { id: 'PRODUCT_REPLACE' as AppMode, icon: Box, label: t.modeProduct },
    { id: 'SECONDARY_GENERATION' as AppMode, icon: Copy, label: t.modeSecondary },
    { id: 'IMAGE_EDIT' as AppMode, icon: ImagePlus, label: t.modeEdit },
    { id: 'TRANSLATION' as AppMode, icon: Languages, label: t.modeTranslate },
  ];

  return (
    <div className="w-full px-4 sm:px-6 lg:px-8 max-w-[1400px] mx-auto z-50 mt-4 mb-2 shrink-0">
      <header className="bg-white/70 backdrop-blur-xl border border-white/40 shadow-lg shadow-slate-200/50 rounded-2xl h-16 transition-all duration-300">
        <div className="h-full flex items-center justify-between px-4 sm:px-6 relative">

          {/* Left: Logo */}
          <div className="flex items-center gap-2 shrink-0">
            <div className="bg-gradient-to-br flex items-center justify-center from-brand-500 to-indigo-600 text-white p-1.5 rounded-xl shadow-inner shadow-white/20 ring-1 ring-brand-400/30">
              <img src="/logo.png" alt="Logo" className="w-5 h-5 object-contain" />
            </div>
            <h1 className="text-xl font-display font-bold tracking-tight text-slate-800 hidden sm:block">
              Chroma<span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-600 to-indigo-600">Adapt</span><span className="font-light text-slate-400 ml-1 text-lg">AI</span>
            </h1>
            <h1 className="text-xl font-bold tracking-tight text-brand-600 sm:hidden">CA</h1>
          </div>

          {/* Center: Navigation */}
          <nav className="absolute left-1/2 -translate-x-1/2 flex items-center gap-1 overflow-x-auto max-w-[40vw] sm:max-w-none no-scrollbar">
            {navItems.map((item) => {
              const isActive = currentMode === item.id;
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => onModeChange(item.id)}
                  className={`
                   relative flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-300 whitespace-nowrap overflow-hidden group
                   ${isActive
                      ? 'text-brand-700'
                      : 'text-slate-500 hover:text-slate-900'
                    }
                 `}
                >
                  {isActive && (
                    <div className="absolute inset-0 bg-brand-50/80 rounded-xl -z-10 animate-in fade-in zoom-in-95 duration-200 ring-1 ring-brand-200/50"></div>
                  )}
                  <div className="absolute inset-0 bg-slate-100/50 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10 scale-95 group-hover:scale-100"></div>
                  <Icon size={16} className={`transition-colors duration-300 relative z-10 ${isActive ? 'text-brand-600' : 'text-slate-400 group-hover:text-slate-600'}`} />
                  <span className="hidden md:inline relative z-10">{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right: Actions */}
          <div className="flex items-center gap-2 sm:gap-4 shrink-0">
            <button
              onClick={onToggleLanguage}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full hover:bg-slate-100 text-sm font-medium text-slate-600 transition-colors"
            >
              <Globe size={14} />
              <span className="hidden sm:inline">{language === 'en' ? '中文' : 'English'}</span>
              <span className="sm:hidden">{language === 'en' ? 'CN' : 'EN'}</span>
            </button>
            <div className="h-4 w-px bg-slate-200 hidden sm:block"></div>
            <button
              onClick={onReset}
              className="text-sm text-slate-500 hover:text-brand-600 transition-colors px-2"
            >
              {t.reset}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile nav fallback */}
      <nav className="lg:hidden flex items-center gap-2 overflow-x-auto no-scrollbar mt-3 px-2">
        {navItems.map((item) => {
          const isActive = currentMode === item.id;
          const Icon = item.icon;
          return (
            <button
              key={`mobile-${item.id}`}
              onClick={() => onModeChange(item.id)}
              className={`
                   flex items-center justify-center p-2.5 rounded-xl text-sm transition-all duration-300 shrink-0
                   ${isActive
                  ? 'bg-brand-100 text-brand-700 shadow-sm border border-brand-200/50'
                  : 'bg-white/50 text-slate-500 border border-transparent'
                }
                 `}
            >
              <Icon size={18} />
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default Header;