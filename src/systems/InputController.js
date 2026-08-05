export class InputController {
  constructor(scene) {
    this.keys = scene.input.keyboard.addKeys({
      left: 'A', right: 'D', jump: 'W', down: 'S', slide: 'SHIFT',
      attack: 'J', skill1: 'Q', skill2: 'E', skill3: 'R',
    });
  }

  read() {
    const k = this.keys;
    return {
      axisX: Number(k.right.isDown) - Number(k.left.isDown),
      down: k.down.isDown,
      slide: k.slide.isDown,
      jumpPressed: Phaser.Input.Keyboard.JustDown(k.jump),
      attackPressed: Phaser.Input.Keyboard.JustDown(k.attack),
      skill1Pressed: Phaser.Input.Keyboard.JustDown(k.skill1),
      skill2Pressed: Phaser.Input.Keyboard.JustDown(k.skill2),
      skill3Pressed: Phaser.Input.Keyboard.JustDown(k.skill3),
    };
  }
}
