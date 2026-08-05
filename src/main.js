import Phaser from 'phaser';
import './styles.css';
import { BootScene } from './scenes/BootScene.js';
import { MenuScene } from './scenes/MenuScene.js';
import { FightScene } from './scenes/FightScene.js';
import { UIScene } from './scenes/UIScene.js';
import { AssetGeneratorController } from './ui/AssetGeneratorController.js';

const game = new Phaser.Game({
  type: Phaser.AUTO,
  parent: 'game-container',
  width: 1280,
  height: 720,
  backgroundColor: '#11162d',
  physics: { default: 'arcade', arcade: { gravity: { y: 1650 }, debug: false } },
  scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
  scene: [BootScene, MenuScene, FightScene, UIScene],
});

new AssetGeneratorController(game);
