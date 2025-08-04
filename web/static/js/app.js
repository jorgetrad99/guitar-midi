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
            console.log('🔌 JS: Cargando datos del sistema...');
            this.setLoading(true);
            
            // Load system status (includes presets and effects)
            console.log('📡 JS: Enviando petición a /api/system/status');
            const response = await fetch('/api/system/status');
            console.log('📥 JS: Respuesta status del sistema:', response.status);
            
            const data = await response.json();
            console.log('📋 JS: Datos del sistema:', data);
            
            if (data.success) {
                this.presets = data.presets || {};
                this.effects = data.effects || {};
                this.currentInstrument = data.current_instrument || 0;
                
                this.renderPresets();
                this.updateCurrentInstrument();
                this.updateEffectValues();
                this.loadControllers();
                
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
        
        // Load specific tab data if needed
        if (tabName === 'controllers') {
            this.loadControllers();
        }
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
            console.log(`❌ JS: Preset ${pc} no configurado`);
            this.showStatus('❌ Preset no configurado', 'error');
            return;
        }

        try {
            console.log(`🎹 JS: Activando preset ${pc} (${preset.name})`);
            this.setLoading(true);

            const response = await fetch(`/api/instruments/${pc}/activate`, {
                method: 'POST'
            });
            
            console.log('📥 JS: Respuesta cambio instrumento, status:', response.status);
            const data = await response.json();
            console.log('📋 JS: Resultado cambio instrumento:', data);

            if (data.success) {
                this.currentInstrument = pc;
                this.updateCurrentInstrument();
                this.updatePresetButtons();
                this.showStatus(`✅ ${preset.name} activado`, 'success');
            } else {
                this.showStatus('❌ Error activando preset', 'error');
            }
        } catch (error) {
            console.error('❌ JS: Error changing instrument:', error);
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
            console.log(`🎛️ JS: Enviando efecto ${effectName} = ${value}%`);
            
            // Update UI immediately for responsiveness
            this.updateEffectDisplay(effectName, value);

            const data = {};
            data[effectName] = value;

            console.log('📡 JS: Datos a enviar:', data);
            
            const response = await fetch('/api/effects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            console.log('📥 JS: Respuesta recibida, status:', response.status);
            
            const result = await response.json();
            console.log('📋 JS: Resultado:', result);
            
            if (result.success) {
                this.effects[effectName] = value;
                this.showStatus(`🎛️ ${this.getEffectLabel(effectName)}: ${value}%`, 'success');
            } else {
                // Revert UI change if API call failed
                this.updateEffectDisplay(effectName, this.effects[effectName] || 0);
                this.showStatus('❌ Error aplicando efecto', 'error');
            }
        } catch (error) {
            console.error('❌ JS: Error updating effect:', error);
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

    async loadControllers() {
        try {
            console.log('🎛️ JS: Cargando controladores...');
            
            const response = await fetch('/api/controllers');
            const data = await response.json();
            
            console.log('📋 JS: Controladores obtenidos:', data);
            
            if (data.success) {
                this.renderControllers(data.controllers, data.types);
            } else {
                this.renderControllersError('Error cargando controladores');
            }
        } catch (error) {
            console.error('❌ JS: Error loading controllers:', error);
            this.renderControllersError('Error de conexión');
        }
    }

    renderControllers(controllers, types) {
        const container = document.getElementById('controllersContainer');
        if (!container) return;

        if (Object.keys(controllers).length === 0) {
            container.innerHTML = `
                <div class="text-center" style="padding: 40px 20px; opacity: 0.7;">
                    <div style="font-size: 2rem; margin-bottom: 15px;">🔌</div>
                    <p>No hay controladores conectados</p>
                    <p style="font-size: 0.9rem; margin-top: 10px;">Conecta un dispositivo MIDI para empezar</p>
                </div>
            `;
            return;
        }

        let html = '';
        Object.entries(controllers).forEach(([controllerName, controllerInfo]) => {
            const type = controllerInfo.type;
            const typeInfo = types[type] || {};
            
            html += `
                <div class="controller-card" data-controller="${controllerName}">
                    <div class="controller-header">
                        <div class="controller-icon">${this.getControllerIcon(type)}</div>
                        <div class="controller-info">
                            <h3 class="controller-name">${controllerName}</h3>
                            <p class="controller-type">${typeInfo.name || type}</p>
                        </div>
                        <div class="controller-status ${controllerInfo.connected ? 'connected' : 'disconnected'}">
                            ${controllerInfo.connected ? '✅' : '❌'}
                        </div>
                    </div>
                    <div class="controller-presets" id="presets-${controllerName}">
                        <div class="loading">Cargando presets...</div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

        // Load presets for each controller
        Object.keys(controllers).forEach(controllerName => {
            this.loadControllerPresets(controllerName);
        });
    }

    renderControllersError(message) {
        const container = document.getElementById('controllersContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="text-center" style="padding: 40px 20px; opacity: 0.7;">
                <div style="font-size: 2rem; margin-bottom: 15px;">❌</div>
                <p>${message}</p>
                <button onclick="window.guitarMIDIApp.loadControllers()" style="margin-top: 15px; padding: 8px 16px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                    🔄 Reintentar
                </button>
            </div>
        `;
    }

    async loadControllerPresets(controllerName) {
        try {
            const response = await fetch(`/api/controllers/${controllerName}/presets`);
            const data = await response.json();
            
            if (data.success) {
                this.renderControllerPresets(controllerName, data.presets, data.current_preset);
            } else {
                this.renderControllerPresetsError(controllerName, data.error);
            }
        } catch (error) {
            console.error(`❌ JS: Error loading presets for ${controllerName}:`, error);
            this.renderControllerPresetsError(controllerName, 'Error de conexión');
        }
    }

    renderControllerPresets(controllerName, presets, currentPreset) {
        const container = document.getElementById(`presets-${controllerName}`);
        if (!container) return;

        if (Object.keys(presets).length === 0) {
            container.innerHTML = '<div class="no-presets">Sin presets configurados</div>';
            return;
        }

        let html = '<div class="preset-grid-small">';
        Object.entries(presets).forEach(([presetId, presetInfo]) => {
            const isActive = parseInt(presetId) === currentPreset;
            html += `
                <button class="preset-btn-small ${isActive ? 'active' : ''}" 
                        onclick="window.guitarMIDIApp.setControllerPreset('${controllerName}', ${presetId})"
                        title="${presetInfo.name}">
                    <div class="preset-id">${presetId}</div>
                    <div class="preset-icon">${presetInfo.icon || '🎵'}</div>
                    <div class="preset-name">${presetInfo.name}</div>
                </button>
            `;
        });
        html += '</div>';

        container.innerHTML = html;
    }

    renderControllerPresetsError(controllerName, error) {
        const container = document.getElementById(`presets-${controllerName}`);
        if (!container) return;

        container.innerHTML = `
            <div class="preset-error">
                <div style="color: #f44336; font-size: 0.9rem;">❌ ${error}</div>
                <button onclick="window.guitarMIDIApp.loadControllerPresets('${controllerName}')" 
                        style="margin-top: 8px; padding: 4px 8px; font-size: 0.8rem; background: var(--primary); color: white; border: none; border-radius: 3px; cursor: pointer;">
                    🔄 Reintentar
                </button>
            </div>
        `;
    }

    async setControllerPreset(controllerName, presetId) {
        try {
            console.log(`🎛️ JS: Activando preset ${presetId} en controlador ${controllerName}`);
            
            const response = await fetch(`/api/controllers/${controllerName}/preset/${presetId}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showStatus(`✅ ${controllerName}: ${data.preset_name}`, 'success');
                // Reload controller presets to update active state
                this.loadControllerPresets(controllerName);
            } else {
                this.showStatus(`❌ Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('❌ JS: Error setting controller preset:', error);
            this.showStatus('❌ Error de conexión', 'error');
        }
    }

    getControllerIcon(type) {
        const icons = {
            'mvave_pocket': '🥁',
            'hexaphonic': '🎸',
            'midi_captain': '🎚️'
        };
        return icons[type] || '🎛️';
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.guitarMIDIApp = new GuitarMIDIApp();
});

// Export for use in other modules
window.GuitarMIDIApp = GuitarMIDIApp;