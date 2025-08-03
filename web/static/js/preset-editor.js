/**
 * Guitar-MIDI Complete System - Preset Editor
 * Handles preset configuration and instrument selection
 */

class PresetEditor {
    constructor() {
        this.currentPresetId = null;
        this.selectedInstrument = null;
        this.instrumentLibrary = {};
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInstrumentLibrary();
    }

    setupEventListeners() {
        // Close modal when clicking outside
        const modal = document.getElementById('presetModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.close();
                }
            });
        }

        // Close button
        const closeBtn = document.querySelector('.close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        // Save button
        const saveBtn = document.querySelector('.save-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.savePreset());
        }

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen()) {
                this.close();
            }
        });
    }

    async loadInstrumentLibrary() {
        try {
            const response = await fetch('/api/instruments/library');
            const data = await response.json();

            if (data.success) {
                this.instrumentLibrary = data.instruments;
                console.log('✅ Instrument library loaded:', Object.keys(this.instrumentLibrary).length, 'categories');
            } else {
                throw new Error(data.error || 'Failed to load instrument library');
            }
        } catch (error) {
            console.error('Error loading instrument library:', error);
            this.showError('Error cargando instrumentos: ' + error.message);
        }
    }

    open(presetId, currentPreset = null) {
        this.currentPresetId = presetId;
        this.selectedInstrument = null;

        // Update modal title
        const titleEl = document.getElementById('editingPresetNumber');
        if (titleEl) {
            titleEl.textContent = presetId;
        }

        // Render instrument categories
        this.renderInstrumentCategories();

        // Show modal
        const modal = document.getElementById('presetModal');
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        // Pre-select current instrument if available
        if (currentPreset && currentPreset.program !== undefined) {
            this.preselectInstrument(currentPreset);
        }
    }

    close() {
        const modal = document.getElementById('presetModal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }

        this.currentPresetId = null;
        this.selectedInstrument = null;
    }

    isOpen() {
        const modal = document.getElementById('presetModal');
        return modal && modal.classList.contains('active');
    }

    renderInstrumentCategories() {
        const container = document.getElementById('instrumentCategories');
        if (!container) return;

        container.innerHTML = '';

        if (Object.keys(this.instrumentLibrary).length === 0) {
            container.innerHTML = `
                <div class="category-section">
                    <div class="text-center" style="padding: 20px; opacity: 0.7;">
                        <p>🔄 Cargando instrumentos...</p>
                        <p style="font-size: 0.9rem; margin-top: 10px;">Si persiste, verifica la conexión con FluidSynth</p>
                    </div>
                </div>
            `;
            return;
        }

        Object.entries(this.instrumentLibrary).forEach(([category, instruments]) => {
            const section = document.createElement('div');
            section.className = 'category-section';

            const title = document.createElement('div');
            title.className = 'category-title';
            title.innerHTML = `${this.getCategoryIcon(category)} ${category}`;
            section.appendChild(title);

            const list = document.createElement('div');
            list.className = 'instrument-list';

            instruments.forEach(instrument => {
                const option = document.createElement('div');
                option.className = 'instrument-option';
                option.addEventListener('click', () => this.selectInstrument(instrument, option));

                option.innerHTML = `
                    <div class="instrument-icon">${instrument.icon || '🎵'}</div>
                    <div class="instrument-info">
                        <div class="instrument-name">${instrument.name}</div>
                        <div class="instrument-details">
                            Program: ${instrument.program} | Bank: ${instrument.bank} | Channel: ${instrument.channel}
                        </div>
                    </div>
                `;

                list.appendChild(option);
            });

            section.appendChild(list);
            container.appendChild(section);
        });
    }

    selectInstrument(instrument, element) {
        // Remove previous selection
        document.querySelectorAll('.instrument-option').forEach(opt => {
            opt.classList.remove('selected');
        });

        // Add selection to clicked element
        element.classList.add('selected');
        this.selectedInstrument = instrument;

        // Enable save button
        const saveBtn = document.querySelector('.save-btn');
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.textContent = `💾 Guardar "${instrument.name}"`;
        }
    }

    preselectInstrument(currentPreset) {
        // Try to find and select the current instrument
        setTimeout(() => {
            const options = document.querySelectorAll('.instrument-option');
            options.forEach(option => {
                const nameEl = option.querySelector('.instrument-name');
                if (nameEl && nameEl.textContent.trim() === currentPreset.name) {
                    option.click();
                }
            });
        }, 100);
    }

    async savePreset() {
        if (!this.selectedInstrument || this.currentPresetId === null) {
            this.showError('Selecciona un instrumento antes de guardar');
            return;
        }

        try {
            const saveBtn = document.querySelector('.save-btn');
            if (saveBtn) {
                saveBtn.disabled = true;
                saveBtn.textContent = '💾 Guardando...';
            }

            const presetData = {
                name: this.selectedInstrument.name,
                program: this.selectedInstrument.program,
                bank: this.selectedInstrument.bank,
                channel: this.selectedInstrument.channel,
                icon: this.selectedInstrument.icon || '🎵'
            };

            const response = await fetch(`/api/presets/${this.currentPresetId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(presetData)
            });

            const data = await response.json();

            if (data.success) {
                // Update main app
                if (window.guitarMIDIApp) {
                    window.guitarMIDIApp.updatePreset(this.currentPresetId, data.preset);
                }

                this.showSuccess(`✅ Preset ${this.currentPresetId} actualizado`);
                
                // Close modal after brief delay
                setTimeout(() => {
                    this.close();
                }, 1000);
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        } catch (error) {
            console.error('Error saving preset:', error);
            this.showError('Error guardando preset: ' + error.message);
        } finally {
            const saveBtn = document.querySelector('.save-btn');
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = '💾 Guardar Preset';
            }
        }
    }

    getCategoryIcon(category) {
        const icons = {
            'Piano': '🎹',
            'Chromatic Percussion': '🔔',
            'Organ': '🎹',
            'Guitar': '🎸',
            'Bass': '🎸',
            'Strings': '🎻',
            'Ensemble': '🎭',
            'Brass': '🎺',
            'Reed': '🎷',
            'Pipe': '🪈',
            'Synth Lead': '🎛️',
            'Synth Pad': '🌊',
            'Synth Effects': '✨',
            'Ethnic': '🌍',
            'Percussive': '🥁',
            'Sound Effects': '🔊',
            'Drums': '🥁'
        };
        return icons[category] || '🎵';
    }

    showError(message) {
        if (window.guitarMIDIApp) {
            window.guitarMIDIApp.showStatus('❌ ' + message, 'error');
        } else {
            console.error(message);
            alert(message);
        }
    }

    showSuccess(message) {
        if (window.guitarMIDIApp) {
            window.guitarMIDIApp.showStatus(message, 'success');
        } else {
            console.log(message);
        }
    }

    // Public method to refresh instrument library
    async refreshLibrary() {
        await this.loadInstrumentLibrary();
        if (this.isOpen()) {
            this.renderInstrumentCategories();
        }
    }
}

// Initialize preset editor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.PresetEditor = new PresetEditor();
});

// Export for use in other modules
window.PresetEditorClass = PresetEditor;