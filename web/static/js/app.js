/**
 * Guitar-MIDI Complete System - Main Application Logic
 */

class GuitarMIDIApp {
    constructor() {
        this.currentInstrument = 0;
        this.presets = {};
        this.effects = {};
        this.isLoading = false;
        
        this.init();
    }

    init() {
        console.log('🎸 Guitar-MIDI Complete System - Initializing...');
        
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.loadSystemData();
        
        console.log('✅ Guitar-MIDI App initialized');
    }

    setupEventListeners() {
        // Navigation tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                if (tabName) {
                    this.showTab(tabName);
                }
            });
        });

        // Panic button
        const panicBtn = document.querySelector('.panic-btn');
        if (panicBtn) {
            panicBtn.addEventListener('click', () => this.panic());
        }

        // Effect sliders
        document.querySelectorAll('.control-slider').forEach(slider => {
            slider.addEventListener('input', (e) => {
                const effect = e.target.dataset.effect;
                const value = parseInt(e.target.value);
                this.updateEffect(effect, value);
            });
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in inputs or modal is open
            if (e.target.tagName === 'INPUT' || 
                document.querySelector('.modal.active')) {
                return;
            }

            if (e.key === 'p' || e.key === 'P') {
                e.preventDefault();
                this.panic();
            } else if (e.key >= '0' && e.key <= '7') {
                e.preventDefault();
                const pc = parseInt(e.key);
                this.changeInstrument(pc);
            }
        });
    }

    async loadSystemData() {
        try {
            this.setLoading(true);
            
            // Load system status (includes presets and effects)
            const response = await fetch('/api/system/status');
            const data = await response.json();
            
            if (data.success) {
                this.presets = data.presets || {};
                this.effects = data.effects || {};
                this.currentInstrument = data.current_instrument || 0;
                
                this.renderPresets();
                this.updateCurrentInstrument();
                this.updateEffectValues();
                
                this.showStatus('✅ Sistema cargado', 'success');
            } else {
                throw new Error('Failed to load system data');
            }
        } catch (error) {
            console.error('Error loading system data:', error);
            this.showStatus('❌ Error cargando sistema', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    showTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');
    }

    renderPresets() {
        const grid = document.getElementById('presetGrid');
        if (!grid) return;

        grid.innerHTML = '';

        for (let i = 0; i < 8; i++) {
            const preset = this.presets[i] || {
                name: 'Sin configurar',
                icon: '❓'
            };

            const presetBtn = document.createElement('div');
            presetBtn.className = `preset-btn ${i === this.currentInstrument ? 'active' : ''}`;
            presetBtn.addEventListener('click', () => this.changeInstrument(i));

            presetBtn.innerHTML = `
                <div class="preset-number">${i}</div>
                <button class="edit-btn" data-preset="${i}" title="Editar preset">✏️</button>
                <div class="preset-icon">${preset.icon}</div>
                <div class="preset-name">${preset.name}</div>
            `;

            // Add edit button listener
            const editBtn = presetBtn.querySelector('.edit-btn');
            editBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.openPresetEditor(i);
            });

            grid.appendChild(presetBtn);
        }
    }

    async changeInstrument(pc) {
        if (this.isLoading) return;

        const preset = this.presets[pc];
        if (!preset) {
            this.showStatus('❌ Preset no configurado', 'error');
            return;
        }

        try {
            this.setLoading(true);

            const response = await fetch(`/api/instruments/${pc}/activate`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                this.currentInstrument = pc;
                this.updateCurrentInstrument();
                this.updatePresetButtons();
                this.showStatus(`✅ ${preset.name} activado`, 'success');
            } else {
                this.showStatus('❌ Error activando preset', 'error');
            }
        } catch (error) {
            console.error('Error changing instrument:', error);
            this.showStatus('❌ Error de conexión', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    updateCurrentInstrument() {
        const preset = this.presets[this.currentInstrument];
        if (!preset) return;

        const iconEl = document.getElementById('currentIcon');
        const nameEl = document.getElementById('currentName');
        const pcEl = document.getElementById('currentPC');

        if (iconEl) iconEl.textContent = preset.icon;
        if (nameEl) nameEl.textContent = preset.name;
        if (pcEl) pcEl.textContent = this.currentInstrument;
    }

    updatePresetButtons() {
        document.querySelectorAll('.preset-btn').forEach((btn, index) => {
            btn.classList.toggle('active', index === this.currentInstrument);
        });
    }

    async updateEffect(effectName, value) {
        if (this.isLoading) return;

        try {
            // Update UI immediately for responsiveness
            this.updateEffectDisplay(effectName, value);

            const data = {};
            data[effectName] = value;

            const response = await fetch('/api/effects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success) {
                this.effects[effectName] = value;
                this.showStatus(`🎛️ ${this.getEffectLabel(effectName)}: ${value}%`, 'success');
            } else {
                // Revert UI change if API call failed
                this.updateEffectDisplay(effectName, this.effects[effectName] || 0);
                this.showStatus('❌ Error aplicando efecto', 'error');
            }
        } catch (error) {
            console.error('Error updating effect:', error);
            // Revert UI change
            this.updateEffectDisplay(effectName, this.effects[effectName] || 0);
            this.showStatus('❌ Error de conexión', 'error');
        }
    }

    updateEffectDisplay(effectName, value) {
        const slider = document.querySelector(`[data-effect="${effectName}"]`);
        const valueDisplay = document.getElementById(`${effectName.replace(/_/g, '')}Value`);

        if (slider) slider.value = value;
        if (valueDisplay) valueDisplay.textContent = `${value}%`;
    }

    updateEffectValues() {
        Object.entries(this.effects).forEach(([effect, value]) => {
            this.updateEffectDisplay(effect, value);
        });
    }

    getEffectLabel(effectName) {
        const labels = {
            'master_volume': 'Volumen Master',
            'global_reverb': 'Reverb Global',
            'global_chorus': 'Chorus Global',
            'global_cutoff': 'Filtro Cutoff',
            'global_resonance': 'Resonancia'
        };
        return labels[effectName] || effectName;
    }

    async panic() {
        if (this.isLoading) return;

        try {
            this.setLoading(true);

            const response = await fetch('/api/system/panic', {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                this.showStatus('🚨 PANIC - Todo detenido', 'warning');
            } else {
                this.showStatus('❌ Error en PANIC', 'error');
            }
        } catch (error) {
            console.error('Error in panic:', error);
            this.showStatus('❌ Error de conexión', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    openPresetEditor(presetId) {
        // This will be implemented in preset-editor.js
        if (window.PresetEditor) {
            window.PresetEditor.open(presetId, this.presets[presetId]);
        } else {
            this.showStatus('❌ Editor no disponible', 'error');
        }
    }

    showStatus(message, type = 'success') {
        const statusEl = document.getElementById('status');
        if (!statusEl) return;

        const colors = {
            success: '#4CAF50',
            error: '#f44336',
            warning: '#FF9800'
        };

        statusEl.textContent = message;
        statusEl.style.backgroundColor = colors[type] || colors.success;
        statusEl.className = `status ${type}`;

        // Reset after 3 seconds
        setTimeout(() => {
            statusEl.textContent = '✅ Sistema Listo';
            statusEl.style.backgroundColor = colors.success;
            statusEl.className = 'status';
        }, 3000);
    }

    setLoading(loading) {
        this.isLoading = loading;
        const body = document.body;
        
        if (loading) {
            body.classList.add('loading');
        } else {
            body.classList.remove('loading');
        }
    }

    // Public methods for external access
    refreshData() {
        return this.loadSystemData();
    }

    getCurrentPreset() {
        return this.presets[this.currentInstrument];
    }

    updatePreset(presetId, presetData) {
        this.presets[presetId] = presetData;
        this.renderPresets();
        if (presetId === this.currentInstrument) {
            this.updateCurrentInstrument();
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.guitarMIDIApp = new GuitarMIDIApp();
});

// Export for use in other modules
window.GuitarMIDIApp = GuitarMIDIApp;