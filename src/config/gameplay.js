export const WORLD = { width: 1600, height: 720, floorY: 625 };
export const FIGHTER = {
  maxHealth: 1000, walkSpeed: 260, airSpeed: 210, jumpSpeed: 690,
  slideSpeed: 470, slideJumpSpeed: 620, bodyWidth: 72, bodyHeight: 180,
};
export const ATTACKS = {
  normal: { damage: 70, startup: 90, active: 110, recovery: 220, range: 96, height: 70, knockback: 160 },
  dash: { damage: 110, startup: 110, active: 150, recovery: 320, range: 130, height: 78, knockback: 280, cooldown: 1300 },
  uppercut: { damage: 145, startup: 80, active: 190, recovery: 430, range: 86, height: 150, knockback: 190, cooldown: 2100 },
  projectile: { damage: 120, startup: 190, active: 0, recovery: 350, range: 0, height: 0, knockback: 130, cooldown: 2800 },
};
