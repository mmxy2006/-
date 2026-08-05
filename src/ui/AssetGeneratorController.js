import { AnimeGanService } from '../services/AnimeGanService.js';

export class AssetGeneratorController {
  constructor(game, service = new AnimeGanService()) {
    this.game = game; this.service = service;
    this.characterInput = document.querySelector('#character-file');
    this.backgroundInput = document.querySelector('#background-prompt');
    this.button = document.querySelector('#generate-assets');
    this.status = document.querySelector('#generation-status');
    this.button.addEventListener('click', () => this.generate());
    this.checkBackend();
  }

  async checkBackend() {
    try {
      const health = await this.service.health(AbortSignal.timeout(4000));
      if (!health.zhipu_key_configured) {
        this.button.disabled = true;
        return this.#setStatus('后端已启动，但缺少智谱 API Key；配置后刷新页面', true);
      }
      this.button.disabled = false;
      this.#setStatus('后端已连接，可以生成形象');
    } catch {
      this.button.disabled = true;
      this.#setStatus('未连接后端：请在 8000 端口启动 feature/backend-dev', true);
    }
  }

  async generate() {
    const character = this.characterInput.files[0];
    if (!character) return this.#setStatus('请选择一张人物照片', true);
    this.button.disabled = true;
    this.#setStatus('正在保留本人特征进行动漫风格转换并生成场景…');
    try {
      const assets = await this.service.generateBattleAssets(character, this.backgroundInput.value);
      sessionStorage.setItem('generatedBattleAssets', JSON.stringify(assets));
      this.#setStatus('生成完成，正在载入游戏…');
      this.game.events.emit('assets:generated', assets);
    } catch (error) {
      this.#setStatus(error.message || '形象生成失败', true);
    } finally {
      this.checkBackend();
    }
  }

  #setStatus(message, error = false) {
    this.status.textContent = message;
    this.status.classList.toggle('error', error);
  }
}
