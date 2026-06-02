/**
 * Saira Universal Speech — har device ke liye
 * STT: Web Speech API (Chrome/Edge/Safari) → fallback MediaRecorder + /speech/transcribe (Groq Whisper)
 * TTS: Browser speechSynthesis → fallback /speech/speak (server MP3)
 */
(function (global) {
  'use strict';

  function stripForSpeech(text) {
    return String(text || '')
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/_([^_]+)_/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/#{1,6}\s*/g, '')
      .replace(/\[Brain:[^\]]+\]/gi, '')
      .trim();
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  class SairaSpeech {
    constructor(opts = {}) {
      this.onTranscript = opts.onTranscript || (() => {});
      this.onError = opts.onError || (() => {});
      this.onStatus = opts.onStatus || (() => {});
      this.lang = opts.lang || 'hi-IN';

      this.listening = false;
      this.mode = 'none';
      this.recognition = null;
      this.mediaRecorder = null;
      this.mediaStream = null;
      this.chunks = [];
      this.serverTtsOk = false;
      this.voices = [];

      this._bindSynthVoices();
      this._detectMode();
      this._checkServer();
    }

    _bindSynthVoices() {
      const load = () => {
        this.voices = global.speechSynthesis?.getVoices() || [];
      };
      load();
      if (global.speechSynthesis) {
        global.speechSynthesis.onvoiceschanged = load;
      }
    }

    async _checkServer() {
      try {
        const r = await fetch('/speech/status');
        const d = await r.json();
        this.serverStt = !!d.whisper;
        this.serverTtsOk = !!d.server_tts;
        this._status(this.mode === 'none' && this.serverStt ? 'server-stt' : this.mode);
      } catch {
        this.serverStt = false;
      }
    }

    _detectMode() {
      const SR = global.SpeechRecognition || global.webkitSpeechRecognition;
      if (SR) {
        this.mode = 'webspeech';
        this.recognition = new SR();
        this.recognition.lang = this.lang;
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;

        this.recognition.onresult = (e) => {
          let text = '';
          for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) text += e.results[i][0].transcript;
          }
          if (text.trim()) {
            this._stopUi();
            this.onTranscript(text.trim());
          }
        };
        this.recognition.onerror = (e) => {
          this._stopUi();
          if (e.error === 'not-allowed') {
            this.onError('Mic permission denied. Browser settings se allow karein.');
          } else if (e.error !== 'aborted' && e.error !== 'no-speech') {
            this._fallbackRecord();
          }
        };
        this.recognition.onend = () => {
          if (this.listening && this.mode === 'webspeech') this._stopUi();
        };
      } else if (navigator.mediaDevices && global.MediaRecorder) {
        this.mode = 'record';
      }
      this._status(this.mode);
    }

    _status(mode) {
      const labels = {
        webspeech: 'Voice: Browser',
        record: 'Voice: Record+AI',
        none: 'Voice: Type only',
      };
      this.onStatus(labels[mode] || mode, mode);
    }

    _pickVoice(langCode) {
      const pref = langCode.slice(0, 2);
      return (
        this.voices.find((v) => v.lang.startsWith(pref)) ||
        this.voices.find((v) => v.lang.startsWith('hi')) ||
        this.voices.find((v) => v.lang.startsWith('en')) ||
        this.voices[0]
      );
    }

    async toggleListen() {
      if (this.listening) {
        await this.stopListen();
        return;
      }
      if (this.mode === 'webspeech') {
        await this._startWebSpeech();
      } else if (this.mode === 'record' || this.serverStt) {
        await this._startRecord();
      } else {
        this.onError('Is device pe mic speech support nahi. Type karke bhejein.');
      }
    }

    async _startWebSpeech() {
      try {
        this.listening = true;
        this._setMicActive(true);
        this.recognition.start();
      } catch (e) {
        this._stopUi();
        await this._startRecord();
      }
    }

    _fallbackRecord() {
      if (this.serverStt || this.mode === 'record') {
        this._startRecord();
      }
    }

    _mimeType() {
      const types = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/ogg;codecs=opus',
      ];
      for (const t of types) {
        if (MediaRecorder.isTypeSupported(t)) return t;
      }
      return '';
    }

    async _startRecord() {
      try {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mime = this._mimeType();
        const opts = mime ? { mimeType: mime } : {};
        this.chunks = [];
        this.mediaRecorder = new MediaRecorder(this.mediaStream, opts);
        this.mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) this.chunks.push(e.data);
        };
        this.mediaRecorder.onstop = () => this._uploadRecording();
        this.mediaRecorder.start();
        this.listening = true;
        this._setMicActive(true);
        this._status('record');
        this._recordTimer = setTimeout(() => this.stopListen(), 15000);
      } catch (e) {
        this._stopUi();
        this.onError('Mic access nahi mila. HTTPS + permission check karein.');
      }
    }

    async stopListen() {
      clearTimeout(this._recordTimer);
      if (this.mode === 'webspeech' && this.recognition && this.listening) {
        try {
          this.recognition.stop();
        } catch (_) {}
      }
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.mediaRecorder.stop();
        this.mediaStream?.getTracks().forEach((t) => t.stop());
      } else {
        this._stopUi();
      }
    }

    async _uploadRecording() {
      this._stopUi();
      if (!this.chunks.length) {
        this.onError('Koi awaaz record nahi hui. Dubara boliye.');
        return;
      }
      const blob = new Blob(this.chunks, { type: this.chunks[0].type || 'audio/webm' });
      const ext = blob.type.includes('mp4') ? 'mp4' : 'webm';
      const fd = new FormData();
      fd.append('audio', blob, `voice.${ext}`);
      fd.append('language', 'hi');

      this.onStatus('Voice: Transcribing…', 'busy');
      try {
        const res = await fetch('/speech/transcribe', { method: 'POST', body: fd });
        const data = await res.json();
        if (res.ok && data.text) {
          this.onTranscript(data.text);
        } else {
          this.onError(data.error || 'Speech samajh nahi aayi.');
        }
      } catch {
        this.onError('Server speech error. Internet check karein.');
      }
      this._status(this.mode);
    }

    _setMicActive(on) {
      const btn = document.getElementById('mic-trigger');
      const icon = document.getElementById('mic-icon');
      if (btn) btn.classList.toggle('mic-active', on);
      if (icon) icon.textContent = on ? '🛑' : '🎤';
    }

    _stopUi() {
      this.listening = false;
      this._setMicActive(false);
      this.mediaStream?.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }

    async speak(text) {
      const clean = stripForSpeech(text);
      if (!clean) return;

      const browserOk = await this._browserSpeak(clean);
      if (browserOk) return;

      if (!this.serverTtsOk) return;
      await this._serverSpeak(clean);
    }

    _browserSpeak(clean) {
      return new Promise((resolve) => {
        if (!global.speechSynthesis) return resolve(false);
        try {
          global.speechSynthesis.cancel();
          const u = new SpeechSynthesisUtterance(clean);
          u.lang = this.lang;
          const v = this._pickVoice(this.lang);
          if (v) u.voice = v;
          u.rate = 0.95;
          u.onend = () => resolve(true);
          u.onerror = () => resolve(false);
          global.speechSynthesis.speak(u);
        } catch (_) {
          resolve(false);
        }
      });
    }

    async _serverSpeak(clean) {
      try {
        const res = await fetch('/speech/speak', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: clean, lang: 'hi' }),
        });
        if (!res.ok) return;
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => URL.revokeObjectURL(url);
        await audio.play();
      } catch (_) {}
    }
  }

  global.SairaSpeech = SairaSpeech;
  global.SairaSpeechUtil = { escapeHtml, stripForSpeech };
})(window);
