const DEFAULT_BASE_URL = import.meta.env.VITE_ANIMEGAN_API_URL || 'http://127.0.0.1:8000';

export class AnimeGanService {
  constructor(baseUrl = DEFAULT_BASE_URL) { this.baseUrl = baseUrl; }

  async health(signal) { return this.#request('/api/health', { signal }); }

  async generateCharacter(file, signal) {
    const form = new FormData();
    form.append('file', file);
    const analyzed = await this.#request('/api/v1/avatars/analyze', { method: 'POST', body: form, signal });
    const composed = await this.#request('/api/v1/avatars/compose', {
      method: 'POST', signal,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ avatar_id: analyzed.avatar_id, features: analyzed.features, with_fancy: false }),
    });
    return { avatarId: composed.avatar_id, imageUrl: this.resolveUrl(composed.image.url), features: analyzed.features };
  }

  async generateBackground(prompt, signal) {
    const result = await this.#request('/api/v1/backgrounds/cartoonize', {
      method: 'POST', signal,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: prompt.trim() }),
    });
    return { backgroundId: result.background_id, imageUrl: this.resolveUrl(result.image.url), scene: result.scene };
  }

  async packageGame(avatarId, backgroundId, signal) {
    const result = await this.#request('/api/v1/games/package', {
      method: 'POST', signal,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        avatar_id: avatarId,
        background_id: backgroundId,
        difficulty: 'normal',
        duration_sec: 60,
        heart_count: 3,
        coin_count: 20,
      }),
    });
    return {
      gameId: result.game_id,
      backgroundUrl: this.resolveUrl(result.background.url),
      playerFrames: {
        run: result.character.run_frames.map((frame) => this.resolveUrl(frame.url)),
        jump: this.resolveUrl(result.character.jump_frame.url),
      },
      gameConfig: result.config,
      obstacles: result.obstacles.map((item) => ({ ...item, imageUrl: this.resolveUrl(item.image.url) })),
      coin: { ...result.coin_sprite, imageUrl: this.resolveUrl(result.coin_sprite.image.url) },
    };
  }

  async generateBattleAssets(characterFile, backgroundPrompt, signal) {
    const prompt = backgroundPrompt?.trim() || '阳光明媚的城市屋顶，适合作为横版格斗游戏竞技场';
    const [character, background] = await Promise.all([
      this.generateCharacter(characterFile, signal),
      this.generateBackground(prompt, signal),
    ]);
    return {
      playerUrl: character.imageUrl,
      playerFrames: null,
      backgroundUrl: background.imageUrl,
      opponentUrl: null,
      avatarId: character.avatarId,
      backgroundId: background.backgroundId,
      gameId: null,
      gameConfig: null,
      obstacles: [],
      coin: null,
    };
  }

  resolveUrl(path) {
    return new URL(path, `${this.baseUrl.replace(/\/$/, '')}/`).href;
  }

  async #request(path, options) {
    const response = await fetch(`${this.baseUrl.replace(/\/$/, '')}${path}`, options);
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `后端请求失败 (${response.status})`);
    }
    return response.json();
  }
}

export const createBattleAssets = ({
  playerUrl = null, opponentUrl = null, backgroundUrl = null,
  playerFrames = null, gameId = null, gameConfig = null, obstacles = [], coin = null,
} = {}) => ({
  playerUrl, opponentUrl, backgroundUrl, playerFrames, gameId, gameConfig, obstacles, coin,
});
