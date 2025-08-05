/**
 * Guitar-MIDI Complete System - Main Application Logic
 */

class GuitarMIDIApp {
    constructor() {
        this.currentInstrument = 0;
        this.presets = {};
        this.effects = {};
        this.isLoading = false;
        
        // Control del panel lateral
        this.selectedController = null;
        this.controllers = {};
        
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

        // Refresh controllers button
        const refreshBtn = document.querySelector('.refresh-controllers');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadControllers());
        }
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
                this.loadControllersSidebar();
                
                // Asegurar que está en vista del sistema al inicio
                this.showSystemPresets();
                
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
        
        // No need to load controllers per tab anymore
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
            console.log(`🎹 JS: Activando preset del sistema ${pc} (${preset.name})`);
            this.setLoading(true);

            const response = await fetch(`/api/instruments/${pc}/activate`, {
                method: 'POST'
            });
            
            console.log('📥 JS: Respuesta cambio instrumento del sistema, status:', response.status);
            const data = await response.json();
            console.log('📋 JS: Resultado cambio instrumento del sistema:', data);

            if (data.success) {
                this.currentInstrument = pc;
                this.updateCurrentInstrument();
                this.updatePresetButtons();
                this.showStatus(`✅ Sistema: ${preset.name} activado`, 'success');
            } else {
                this.showStatus('❌ Error activando preset del sistema', 'error');
                console.error('Error details:', data);
            }
        } catch (error) {
            console.error('❌ JS: Error changing system instrument:', error);
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

    async loadControllersSidebar() {
        try {
            console.log('🎛️ JS: Cargando controladores en sidebar...');
            
            const response = await fetch('/api/controllers');
            const data = await response.json();
            
            console.log('📋 JS: Controladores obtenidos:', data);
            
            if (data.success) {
                this.controllers = data.controllers;
                this.renderControllersSidebar(data.controllers);
            } else {
                this.renderControllersSidebarError('Error cargando controladores');
            }
        } catch (error) {
            console.error('❌ JS: Error loading controllers:', error);
            this.renderControllersSidebarError('Error de conexión');
        }
    }

    renderControllersSidebar(controllers) {
        const container = document.getElementById('controllersList');
        if (!container) return;

        if (Object.keys(controllers).length === 0) {
            container.innerHTML = `
                <div class="loading-controllers">
                    <div>🔌</div>
                    <p>No hay controladores</p>
                </div>
            `;
            return;
        }

        let html = '';
        Object.entries(controllers).forEach(([controllerName, controllerInfo]) => {
            const type = controllerInfo.type;
            const isActive = this.selectedController === controllerName;
            
            html += `
                <div class="controller-item ${isActive ? 'active' : ''}" 
                     data-controller="${controllerName}"
                     onclick="window.guitarMIDIApp.selectController('${controllerName}')">
                    <div class="controller-icon">${this.getControllerIcon(type)}</div>
                    <div class="controller-info">
                        <div class="controller-name">${controllerName}</div>
                        <div class="controller-type">${type.replace('_', ' ')}</div>
                    </div>
                    <div class="controller-status">
                        ${controllerInfo.connected ? '✅' : '❌'}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    renderControllersSidebarError(message) {
        const container = document.getElementById('controllersList');
        if (!container) return;

        container.innerHTML = `
            <div class="loading-controllers">
                <div>❌</div>
                <p>${message}</p>
                <button onclick="window.guitarMIDIApp.loadControllersSidebar()" 
                        style="margin-top: 10px; padding: 6px 12px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                    🔄 Reintentar
                </button>
            </div>
        `;
    }

    async selectController(controllerName) {
        try {
            console.log(`🎛️ JS: Seleccionando controlador: ${controllerName}`);
            
            this.selectedController = controllerName;
            
            // Actualizar UI para mostrar el controlador seleccionado
            this.renderControllersSidebar(this.controllers);
            
            // Cambiar la vista de presets para mostrar los del controlador
            await this.showControllerPresets(controllerName);
            
            // Asegurarse de que estamos en la pestaña de presets
            this.showTab('presets');
            
        } catch (error) {
            console.error('❌ JS: Error selecting controller:', error);
        }
    }

    async loadSelectedControllerPresets(controllerName) {
        try {
            const container = document.getElementById('selectedControllerPresets');
            if (!container) return;
            
            // Mostrar loading
            container.innerHTML = `
                <div class="loading-controllers">
                    <div>🔄</div>
                    <p>Cargando presets...</p>
                </div>
            `;
            
            const response = await fetch(`/api/controllers/${controllerName}/presets`);
            const data = await response.json();
            
            if (data.success) {
                this.renderSelectedControllerPresets(controllerName, data.presets, data.current_preset);
            } else {
                container.innerHTML = `
                    <div class="loading-controllers">
                        <div>❌</div>
                        <p>Error: ${data.error}</p>
                    </div>
                `;
            }
            
        } catch (error) {
            console.error(`❌ JS: Error loading presets for ${controllerName}:`, error);
            const container = document.getElementById('selectedControllerPresets');
            if (container) {
                container.innerHTML = `
                    <div class="loading-controllers">
                        <div>❌</div>
                        <p>Error de conexión</p>
                    </div>
                `;
            }
        }
    }

    renderSelectedControllerPresets(controllerName, presets, currentPreset) {
        const container = document.getElementById('selectedControllerPresets');
        if (!container) return;

        if (Object.keys(presets).length === 0) {
            container.innerHTML = `
                <div class="no-controller-selected">
                    <div>🎛️</div>
                    <p>Sin presets</p>
                </div>
            `;
            return;
        }

        let html = `<h4 style="margin-bottom: 15px; color: var(--primary);">Presets - ${controllerName}</h4>`;
        
        Object.entries(presets).forEach(([presetId, presetInfo]) => {
            const isActive = parseInt(presetId) === currentPreset;
            
            html += `
                <div class="preset-item ${isActive ? 'active' : ''}" 
                     onclick="window.guitarMIDIApp.setControllerPreset('${controllerName}', ${presetId})">
                    <div class="preset-number">${presetId}</div>
                    <div class="preset-info">
                        <div class="preset-name">${presetInfo.name || 'Preset ' + presetId}</div>
                        <div class="preset-details">Programa ${presetInfo.program || 0}</div>
                    </div>
                    <button class="preset-edit" 
                            onclick="event.stopPropagation(); window.guitarMIDIApp.editControllerPreset('${controllerName}', ${presetId})"
                            title="Editar preset">
                        ✏️
                    </button>
                </div>
            `;
        });

        container.innerHTML = html;
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
                // Recargar presets para actualizar el estado activo
                this.loadSelectedControllerPresets(controllerName);
            } else {
                this.showStatus(`❌ Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('❌ JS: Error setting controller preset:', error);
            this.showStatus('❌ Error de conexión', 'error');
        }
    }

    editControllerPreset(controllerName, presetId) {
        // TODO: Implementar editor de presets para controladores
        console.log(`✏️ JS: Editando preset ${presetId} de ${controllerName}`);
        this.showStatus('🔧 Editor de presets en desarrollo', 'warning');
    }

    async loadControllerPresetsLarge(controllerName) {
        try {
            const container = document.getElementById('controllerPresetsContent');
            if (!container) return;
            
            // Mostrar loading
            container.innerHTML = `
                <div class="loading-controllers">
                    <div>🔄</div>
                    <p>Cargando presets de ${controllerName}...</p>
                </div>
            `;
            
            const response = await fetch(`/api/controllers/${controllerName}/presets`);
            const data = await response.json();
            
            if (data.success) {
                this.renderControllerPresetsLarge(controllerName, data.presets, data.current_preset, data.controller_type);
            } else {
                container.innerHTML = `
                    <div class="loading-controllers">
                        <div>❌</div>
                        <p>Error: ${data.error}</p>
                        <button onclick="window.guitarMIDIApp.loadControllerPresetsLarge('${controllerName}')" 
                                style="margin-top: 10px; padding: 8px 16px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                            🔄 Reintentar
                        </button>
                    </div>
                `;
            }
            
        } catch (error) {
            console.error(`❌ JS: Error loading presets for ${controllerName}:`, error);
            const container = document.getElementById('controllerPresetsContent');
            if (container) {
                container.innerHTML = `
                    <div class="loading-controllers">
                        <div>❌</div>
                        <p>Error de conexión</p>
                        <button onclick="window.guitarMIDIApp.loadControllerPresetsLarge('${controllerName}')" 
                                style="margin-top: 10px; padding: 8px 16px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                            🔄 Reintentar
                        </button>
                    </div>
                `;
            }
        }
    }

    renderControllerPresetsLarge(controllerName, presets, currentPreset, controllerType) {
        const container = document.getElementById('controllerPresetsContent');
        if (!container) return;

        if (Object.keys(presets).length === 0) {
            container.innerHTML = `
                <div class="no-controller-selected-main">
                    <div class="empty-state">
                        <div class="empty-icon">🎛️</div>
                        <h3>Sin Presets</h3>
                        <p>Este controlador no tiene presets configurados</p>
                    </div>
                </div>
            `;
            return;
        }

        let html = `
            <div class="controller-presets-large">
                <div class="controller-presets-header">
                    <div class="controller-presets-title">
                        ${this.getControllerIcon(controllerType)} Presets - ${controllerName}
                    </div>
                    <div style="font-size: 0.9rem; opacity: 0.7;">
                        ${Object.keys(presets).length} presets disponibles
                    </div>
                </div>
                <div class="controller-presets-grid">
        `;
        
        Object.entries(presets).forEach(([presetId, presetInfo]) => {
            const isActive = parseInt(presetId) === currentPreset;
            
            html += `
                <div class="controller-preset-card ${isActive ? 'active' : ''}" 
                     onclick="window.guitarMIDIApp.setControllerPresetLarge('${controllerName}', ${presetId})">
                    <div class="controller-preset-number">${presetId}</div>
                    <div class="controller-preset-icon">${presetInfo.icon || '🎵'}</div>
                    <div class="controller-preset-name">${presetInfo.name || 'Preset ' + presetId}</div>
                    <div class="controller-preset-details">Programa ${presetInfo.program || 0}</div>
                    <button class="controller-preset-edit" 
                            onclick="event.stopPropagation(); window.guitarMIDIApp.editControllerPreset('${controllerName}', ${presetId})"
                            title="Editar preset">
                        ✏️
                    </button>
                </div>
            `;
        });

        html += `
                </div>
                <div style="text-align: center; opacity: 0.8; font-size: 0.9rem; margin-top: 20px;">
                    💡 Haz clic en un preset para activarlo
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    async setControllerPresetLarge(controllerName, presetId) {
        try {
            console.log(`🎛️ JS: Activando preset ${presetId} en controlador ${controllerName} (large view)`);
            
            const response = await fetch(`/api/controllers/${controllerName}/preset/${presetId}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showStatus(`✅ ${controllerName}: ${data.preset_name}`, 'success');
                // Recargar presets para actualizar el estado activo
                this.loadControllerPresetsLarge(controllerName);
            } else {
                this.showStatus(`❌ Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('❌ JS: Error setting controller preset:', error);
            this.showStatus('❌ Error de conexión', 'error');
        }
    }

    // Mantener función para compatibilidad (llamará a la nueva)
    async loadControllers() {
        return this.loadControllersSidebar();
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

    async showControllerPresets(controllerName) {
        try {
            console.log(`🎛️ JS: Mostrando presets de controlador: ${controllerName}`);
            
            // Ocultar vista por defecto y mostrar vista de controlador
            const defaultView = document.getElementById('defaultPresetsView');
            const controllerView = document.getElementById('controllerPresetsView');
            
            if (defaultView) defaultView.style.display = 'none';
            if (controllerView) controllerView.style.display = 'block';
            
            // Cargar presets del controlador
            await this.loadControllerPresetsInMainView(controllerName);
            
        } catch (error) {
            console.error('❌ JS: Error showing controller presets:', error);
        }
    }

    showSystemPresets() {
        try {
            console.log('🎛️ JS: Mostrando presets del sistema');
            
            // Mostrar vista por defecto y ocultar vista de controlador
            const defaultView = document.getElementById('defaultPresetsView');
            const controllerView = document.getElementById('controllerPresetsView');
            
            if (defaultView) defaultView.style.display = 'block';
            if (controllerView) controllerView.style.display = 'none';
            
            // Limpiar controlador seleccionado
            this.selectedController = null;
            this.renderControllersSidebar(this.controllers);
            
        } catch (error) {
            console.error('❌ JS: Error showing system presets:', error);
        }
    }

    async loadControllerPresetsInMainView(controllerName) {
        try {
            const container = document.getElementById('controllerPresetsView');
            if (!container) return;
            
            // Mostrar loading
            container.innerHTML = `
                <div class="loading-controllers">
                    <div>🔄</div>
                    <p>Cargando presets de ${controllerName}...</p>
                </div>
            `;
            
            const response = await fetch(`/api/controllers/${controllerName}/presets`);
            const data = await response.json();
            
            if (data.success) {
                this.renderControllerPresetsInMainView(controllerName, data.presets, data.current_preset, data.controller_type);
            } else {
                container.innerHTML = `
                    <div class="loading-controllers">
                        <div>❌</div>
                        <p>Error: ${data.error}</p>
                        <button onclick="window.guitarMIDIApp.loadControllerPresetsInMainView('${controllerName}')" 
                                style="margin-top: 10px; padding: 8px 16px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                            🔄 Reintentar
                        </button>
                    </div>
                `;
            }
            
        } catch (error) {
            console.error(`❌ JS: Error loading presets for ${controllerName}:`, error);
            const container = document.getElementById('controllerPresetsView');
            if (container) {
                container.innerHTML = `
                    <div class="loading-controllers">
                        <div>❌</div>
                        <p>Error de conexión</p>
                        <button onclick="window.guitarMIDIApp.loadControllerPresetsInMainView('${controllerName}')" 
                                style="margin-top: 10px; padding: 8px 16px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                            🔄 Reintentar
                        </button>
                    </div>
                `;
            }
        }
    }

    renderControllerPresetsInMainView(controllerName, presets, currentPreset, controllerType) {
        const container = document.getElementById('controllerPresetsView');
        if (!container) return;

        if (Object.keys(presets).length === 0) {
            container.innerHTML = `
                <h2 class="section-title">
                    ${this.getControllerIcon(controllerType)} ${controllerName} - Sin Presets
                </h2>
                <div class="no-controller-selected-main">
                    <div class="empty-state">
                        <div class="empty-icon">🎛️</div>
                        <h3>Sin Presets</h3>
                        <p>Este controlador no tiene presets configurados</p>
                        <button onclick="window.guitarMIDIApp.showSystemPresets()" 
                                style="margin-top: 15px; padding: 10px 20px; background: var(--primary); color: white; border: none; border-radius: 8px; cursor: pointer;">
                            🔙 Ver Presets del Sistema
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        let html = `
            <h2 class="section-title">
                ${this.getControllerIcon(controllerType)} Presets - ${controllerName}
                <button onclick="window.guitarMIDIApp.showSystemPresets()" 
                        style="float: right; padding: 8px 16px; background: var(--secondary); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85rem;">
                    🔙 Sistema
                </button>
            </h2>
            <div class="preset-grid">
        `;
        
        Object.entries(presets).forEach(([presetId, presetInfo]) => {
            const isActive = parseInt(presetId) === currentPreset;
            
            html += `
                <div class="preset-btn ${isActive ? 'active' : ''}" 
                     onclick="window.guitarMIDIApp.setControllerPresetMain('${controllerName}', ${presetId})">
                    <div class="preset-number">${presetId}</div>
                    <button class="edit-btn" data-preset="${presetId}" 
                            onclick="event.stopPropagation(); window.guitarMIDIApp.editControllerPreset('${controllerName}', ${presetId})"
                            title="Editar preset">✏️</button>
                    <div class="preset-icon">${presetInfo.icon || '🎵'}</div>
                    <div class="preset-name">${presetInfo.name || 'Preset ' + presetId}</div>
                </div>
            `;
        });

        html += `
            </div>
            <div class="text-center" style="opacity: 0.8; font-size: 0.9rem; margin-top: 20px;">
                💡 Presets del controlador ${controllerName} - ${Object.keys(presets).length} disponibles
            </div>
        `;

        container.innerHTML = html;
    }

    async setControllerPresetMain(controllerName, presetId) {
        try {
            console.log(`🎛️ JS: Activando preset ${presetId} en controlador ${controllerName} (main view)`);
            
            const response = await fetch(`/api/controllers/${controllerName}/preset/${presetId}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showStatus(`✅ ${controllerName}: ${data.preset_name}`, 'success');
                // Recargar presets para actualizar el estado activo
                this.loadControllerPresetsInMainView(controllerName);
            } else {
                this.showStatus(`❌ Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('❌ JS: Error setting controller preset:', error);
            this.showStatus('❌ Error de conexión', 'error');
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.guitarMIDIApp = new GuitarMIDIApp();
});

// Export for use in other modules
window.GuitarMIDIApp = GuitarMIDIApp;