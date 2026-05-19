"""
横スクロールアクションゲーム（マリオ風）- ゴール機能付き拡張版

Pygameを使用した2Dドット絵スタイルの横スクロールアクションゲームの
完全版です。以下の機能を備えています：
- シーン管理（タイトル、ゲーム本編、ゲームクリア、ゲームオーバー）
- プレイヤーの移動・ジャンプ・重力処理
- ブロックによるステージ構築
- 横スクロール（カメラワーク）機能
- ゴール機能（Goal クラス）
- 拡張性の高いオブジェクト指向設計
"""

import pygame
import sys
from typing import Tuple, List, Optional, Sequence
from enum import Enum
from abc import ABC, abstractmethod


# ================== 定数・グローバル設定 ==================

class Config:
    """ゲーム全体の設定値を管理するクラス"""
    
    # 画面設定
    SCREEN_WIDTH: int = 800
    SCREEN_HEIGHT: int = 600
    FPS: int = 60
    
    # 色定義（RGB）
    COLOR_BLACK: Tuple[int, int, int] = (0, 0, 0)
    COLOR_WHITE: Tuple[int, int, int] = (255, 255, 255)
    COLOR_BLUE: Tuple[int, int, int] = (0, 100, 255)
    COLOR_GREEN: Tuple[int, int, int] = (0, 200, 0)
    COLOR_RED: Tuple[int, int, int] = (255, 0, 0)
    COLOR_GRAY: Tuple[int, int, int] = (128, 128, 128)
    COLOR_LIGHT_BLUE: Tuple[int, int, int] = (135, 206, 235)
    COLOR_GOLD: Tuple[int, int, int] = (255, 215, 0)
    COLOR_YELLOW: Tuple[int, int, int] = (255, 255, 0)
    COLOR_DARK_YELLOW: Tuple[int, int, int] = (200, 200, 0)
    
    # プレイヤー設定
    PLAYER_WIDTH: int = 32
    PLAYER_HEIGHT: int = 48
    PLAYER_START_X: int = 100
    PLAYER_START_Y: int = 400
    PLAYER_MOVE_SPEED: int = 5
    PLAYER_JUMP_POWER: int = 15
    
    # 重力設定
    GRAVITY: float = 0.6
    MAX_FALL_SPEED: int = 20
    
    # ブロック設定
    BLOCK_WIDTH: int = 64
    BLOCK_HEIGHT: int = 64
    
    # ゴール設定
    GOAL_WIDTH: int = 50
    GOAL_HEIGHT: int = 80
    GOAL_X: int = 3000  # ゴールのX座標（ワールド座標）
    GOAL_Y: int = 350   # ゴールのY座標（ワールド座標）
    
    # ステージ設定
    STAGE_MAX_X: int = 3100  # ステージの最大X座標

    TIME_LIMIT: float = 300.0
    
    ENEMY_WIDTH: int = 32      # ザコ敵の横幅
    ENEMY_HEIGHT: int = 32     # ザコ敵の縦幅
    ENEMY_SPEED: float = 2.0   # ザコ敵の歩くスピード
class SceneType(Enum):
    """シーンの種類を定義する列挙型"""
    TITLE = 1
    GAME = 2
    GAME_OVER = 3
    GAME_CLEAR = 4


# ================== ブロッククラス ==================

class Block:
    """
    ステージの床や足場を表すクラス
    
    このクラスを継承することで、特殊なギミックブロックを
    簡単に実装できるように設計されています。
    """
    
    def __init__(self, x: int, y: int, width: int = Config.BLOCK_WIDTH,
                 height: int = Config.BLOCK_HEIGHT, color: Tuple[int, int, int] = Config.COLOR_GREEN) -> None:
        """
        ブロックの初期化
        
        Args:
            x: X座標（ワールド座標）
            y: Y座標（ワールド座標）
            width: ブロックの幅（ピクセル）
            height: ブロックの高さ（ピクセル）
            color: ブロックの色（RGB）
        """
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.color: Tuple[int, int, int] = color
    
    def get_rect(self) -> pygame.Rect:
        """
        ブロックの矩形判定オブジェクトを取得
        
        Returns:
            ブロックを表すpygame.Rectオブジェクト
        """
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """
        ブロックを描画（カメラオフセット適用）
        
        Args:
            surface: 描画対象のサーフェス
            camera_x: カメラのX座標オフセット
        """
        # 画面内のX座標を計算
        screen_x: int = self.x - camera_x
        
        # 画面外の場合は描画しない
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        
        # ブロックを描画
        rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        
        # ブロックの枠線を描画（3ドットゲーム風のドット絵効果）
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)


# ================== ゴールクラス ==================

class Goal:
    """
    ステージのゴール（ゴール地点）を表すクラス
    
    プレイヤーがこのゴールに接触するとゲームクリアになります。
    """
    
    def __init__(self, x: int = Config.GOAL_X, y: int = Config.GOAL_Y,
                 width: int = Config.GOAL_WIDTH, height: int = Config.GOAL_HEIGHT) -> None:
        """
        ゴールの初期化
        
        Args:
            x: X座標（ワールド座標）
            y: Y座標（ワールド座標）
            width: ゴールの幅（ピクセル）
            height: ゴールの高さ（ピクセル）
        """
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.color: Tuple[int, int, int] = Config.COLOR_GOLD
    
    def get_rect(self) -> pygame.Rect:
        """
        ゴールの矩形判定オブジェクトを取得
        
        Returns:
            ゴールを表すpygame.Rectオブジェクト
        """
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def check_collision(self, player_rect: pygame.Rect) -> bool:
        """
        プレイヤーとゴールの衝突判定を確認
        
        Args:
            player_rect: プレイヤーの矩形判定オブジェクト
        
        Returns:
            衝突している場合True、していない場合False
        """
        goal_rect: pygame.Rect = self.get_rect()
        return player_rect.colliderect(goal_rect)
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """
        ゴールを描画（カメラオフセット適用）
        
        Args:
            surface: 描画対象のサーフェス
            camera_x: カメラのX座標オフセット
        """
        # 画面内のX座標を計算
        screen_x: int = self.x - camera_x
        
        # 画面外の場合は描画しない
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        
        # ゴールを描画（フラグポール風）
        goal_rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, goal_rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, goal_rect, 3)
        
        # ゴール内に装飾（星を描画）
        center_x: int = screen_x + self.width // 2
        center_y: int = self.y + self.height // 2
        pygame.draw.polygon(surface, Config.COLOR_YELLOW, [
            (center_x, center_y - 8),
            (center_x + 4, center_y - 2),
            (center_x + 8, center_y),
            (center_x + 4, center_y + 4),
            (center_x + 6, center_y + 8),
            (center_x, center_y + 5),
            (center_x - 6, center_y + 8),
            (center_x - 4, center_y + 4),
            (center_x - 8, center_y),
            (center_x - 4, center_y - 2)
        ])


# ================== プレイヤークラス ==================

class Player:
    """
    プレイヤーキャラクターを表すクラス
    
    移動、ジャンプ、重力処理、およびブロックとの当たり判定を
    担当します。このクラスを継承することで、様々なプレイヤーバリエーション
    を実装できます。
    """
    
    def __init__(self, x: int = Config.PLAYER_START_X,
                 y: int = Config.PLAYER_START_Y,
                 width: int = Config.PLAYER_WIDTH,
                 height: int = Config.PLAYER_HEIGHT) -> None:
        """
        プレイヤーの初期化
        
        Args:
            x: 初期X座標（ワールド座標）
            y: 初期Y座標（ワールド座標）
            width: プレイヤーの幅（ピクセル）
            height: プレイヤーの高さ（ピクセル）
        """
        self.x: float = x
        self.y: float = y
        self.width: int = width
        self.height: int = height
        
        # 速度
        self.vx: float = 0.0  # X方向の速度
        self.vy: float = 0.0  # Y方向の速度
        
        # 状態
        self.is_jumping: bool = False  # ジャンプ中フラグ
        self.is_on_ground: bool = True  # 地面に接地中フラグ
        self.color: Tuple[int, int, int] = Config.COLOR_BLUE
        self.facing_right: bool = True  # 向き（右：True、左：False）
    
    def get_rect(self) -> pygame.Rect:
        """
        プレイヤーの矩形判定オブジェクトを取得
        
        Returns:
            プレイヤーを表すpygame.Rectオブジェクト
        """
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
    
    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """
        キー入力を処理してプレイヤーの動作を更新
        
        Args:
            keys: pygame.key.get_pressed()の戻り値
        """
        # 左右の移動処理
        if keys[pygame.K_LEFT]:
            self.vx = -Config.PLAYER_MOVE_SPEED
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vx = Config.PLAYER_MOVE_SPEED
            self.facing_right = True
        else:
            self.vx = 0.0
        
        # ジャンプ処理（地面に接地していて、スペースキーが押された）
        if keys[pygame.K_SPACE] and self.is_on_ground:
            self.vy = -Config.PLAYER_JUMP_POWER
            self.is_jumping = True
            self.is_on_ground = False
    
    def apply_gravity(self) -> None:
        """重力を適用してY方向の速度を更新"""
        # 重力加速度を追加
        self.vy += Config.GRAVITY
        
        # 最大落下速度に制限
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED
    
    def update(self, blocks: List[Block]) -> None:
        """
        プレイヤーの状態を更新
        
        Args:
            blocks: ステージ上のすべてのブロックのリスト
        """
        # 重力を適用
        self.apply_gravity()
        
        # 位置を更新
        self.x += self.vx
        self.y += self.vy
        
        # 接地状態をリセット
        self.is_on_ground = False
        
        # ブロックとの当たり判定
        self._check_block_collisions(blocks)
        
        # 画面下部でゲームオーバー判定
        if self.y > Config.SCREEN_HEIGHT + 100:
            self.reset()
    
    def _check_block_collisions(self, blocks: List[Block]) -> None:
        """
        ブロックとの当たり判定を処理
        
        Args:
            blocks: 判定対象のブロックリスト
        """
        player_rect: pygame.Rect = self.get_rect()
        
        for block in blocks:
            block_rect: pygame.Rect = block.get_rect()
            
            # 矩形が交差しているかチェック
            if not player_rect.colliderect(block_rect):
                continue
            
            # 衝突時の処理
            # Y方向の衝突判定（上下からの衝突を区別）
            overlap_y_from_top: int = player_rect.bottom - block_rect.top
            overlap_y_from_bottom: int = block_rect.bottom - player_rect.top
            
            # X方向の衝突判定（左右からの衝突を区別）
            overlap_x_from_left: int = player_rect.right - block_rect.left
            overlap_x_from_right: int = block_rect.right - player_rect.left
            
            # 最小オーバーラップ方向に応じて対応
            min_overlap: int = min(overlap_y_from_top, overlap_y_from_bottom,
                                   overlap_x_from_left, overlap_x_from_right)
            
            if min_overlap == overlap_y_from_top:
                # プレイヤーがブロックの上から着地
                self.y = block_rect.top - self.height
                self.vy = 0.0
                self.is_on_ground = True
                self.is_jumping = False
            elif min_overlap == overlap_y_from_bottom:
                # プレイヤーがブロックの下に衝突（頭をぶつける）
                self.y = block_rect.bottom
                self.vy = 0.0
            elif min_overlap == overlap_x_from_left:
                # プレイヤーがブロックの左から衝突
                self.x = block_rect.left - self.width
            elif min_overlap == overlap_x_from_right:
                # プレイヤーがブロックの右から衝突
                self.x = block_rect.right
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """
        プレイヤーを描画（カメラオフセット適用）
        
        Args:
            surface: 描画対象のサーフェス
            camera_x: カメラのX座標オフセット
        """
        # 画面内のX座標を計算
        screen_x: int = int(self.x) - camera_x
        screen_y: int = int(self.y)
        
        # プレイヤーの矩形を描画
        rect: pygame.Rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        
        # 枠線を描画
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)
        
        # 顔の簡単な表現（ドット絵風）
        eye_offset: int = 8 if self.facing_right else (self.width - 14)
        pygame.draw.circle(surface, Config.COLOR_BLACK, 
                         (screen_x + eye_offset, screen_y + 12), 2)
    
    def reset(self) -> None:
        """プレイヤーをリセット（ゲームオーバー時など）"""
        self.x = Config.PLAYER_START_X
        self.y = Config.PLAYER_START_Y
        self.vx = 0.0
        self.vy = 0.0
        self.is_jumping = False
        self.is_on_ground = True


# ================== シーン管理 ==================

class Scene(ABC):
    """
    シーンの基底クラス
    
    すべてのシーン（タイトル、ゲーム本編など）はこのクラスを
    継承して実装します。
    """
    
    @abstractmethod
    def handle_input(self, event: pygame.event.EventType) -> None:
        """
        イベント処理
        
        Args:
            event: pygame のイベントオブジェクト
        """
        pass
    
    @abstractmethod
    def update(self) -> Optional[SceneType]:
        """
        シーン状態の更新
        
        Returns:
            シーン切り替え時は対応するSceneType、継続時はNone
        """
        pass
    
    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """
        シーンの描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        pass

# ================== 敵（通常ザコ＆ボス）システム ==================

class Enemy:
    """自動で歩き、壁で反転し、プレイヤーと接触判定を行うシンプルなザコ敵"""
    
    def __init__(self, x: int, y: int) -> None:
        self.x: float = x
        self.y: float = y
        # 後でデザインを当てやすい標準的なサイズ
        self.width: int = Config.ENEMY_WIDTH
        self.height: int = Config.ENEMY_HEIGHT
        self.vx: float = -Config.ENEMY_SPEED  # 最初は左に進む
        self.vy: float = 0.0
        # 仮のデザイン：通常のザコ敵は「赤色の四角」
        self.color: Tuple[int, int, int] = Config.COLOR_RED
        
    def get_rect(self) -> pygame.Rect:
        """衝突判定用の四角形データを返す"""
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        
    def update(self, blocks: List[Block]) -> None:
        """物理演算とブロック（床・壁）との当たり判定"""
        # 重力の適用
        self.vy += Config.GRAVITY
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED
            
        self.x += self.vx
        self.y += self.vy
        
        # 地形との衝突判定＆壁での反転
        enemy_rect = self.get_rect()
        for block in blocks:
            block_rect = block.get_rect()
            if enemy_rect.colliderect(block_rect):
                overlap_x = min(enemy_rect.right - block_rect.left, block_rect.right - enemy_rect.left)
                overlap_y = min(enemy_rect.bottom - block_rect.top, block_rect.bottom - enemy_rect.top)
                
                if overlap_y < overlap_x:
                    if self.vy > 0:  # 床に着地
                        self.y = block_rect.top - self.height
                        self.vy = 0.0
                else:  # 壁にぶつかったら反転
                    if self.vx > 0:
                        self.x = block_rect.left - self.width
                    else:
                        self.x = block_rect.right
                    self.vx *= -1
                    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """仮の姿（シンプルな四角形）として描画"""
        screen_x = int(self.x) - camera_x
        # 画面外なら描画をスキップ
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
            
        rect = pygame.Rect(screen_x, int(self.y), self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)  # 輪郭線


class Boss(Enemy):
    """3回踏まないと倒せない、システム確認用の巨大なボスクラス"""
    
    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        # ラスボスらしく、ザコ敵よりもサイズを大きく設定
        self.width = 80
        self.height = 96
        # 移動スピードはどっしり遅め
        self.vx = -1.2
        # 仮のデザイン：ラスボスは「緑色の大きな四角」
        self.color = (0, 150, 50) 
        
        # ボスの固有システム：体力（HP）
        self.hp: int = 3

    def take_damage(self) -> bool:
        """ダメージを受けた（踏まれた）時の処理"""
        self.hp -= 1
        if self.hp <= 0:
            return True  # 撃破フラグ（消滅）
            
        # ダメージを受けると怒ってスピードが1.5倍になるギミック
        self.vx *= 1.5
        return False  # まだ生きてる
    
# === ここまで追加 ===
class TitleScene(Scene):
    """タイトル画面シーン"""
    
    def __init__(self) -> None:
        """タイトル画面の初期化"""
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        """
        キー入力処理
        
        Args:
            event: pygame のイベントオブジェクト
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # スペースキーでゲーム開始
                return
    
    def update(self) -> Optional[SceneType]:
        """
        更新処理
        
        Returns:
            スペースキーが押されたらゲームシーンに切り替え
        """
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            return SceneType.GAME
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        画面描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        # 背景を描画
        surface.fill(Config.COLOR_LIGHT_BLUE)
        
        # タイトルテキストを描画
        title_text: pygame.Surface = self.title_font.render(
            "FAKE MARIO", True, Config.COLOR_BLACK)
        title_rect: pygame.Rect = title_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 150))
        surface.blit(title_text, title_rect)
        
        # 説明テキストを描画
        instruction_text: pygame.Surface = self.instruction_font.render(
            "Press SPACE to Start", True, Config.COLOR_BLACK)
        instruction_rect: pygame.Rect = instruction_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 350))
        surface.blit(instruction_text, instruction_rect)
        
        # 操作説明を描画
        control_font: pygame.font.Font = pygame.font.Font(None, 30)
        controls: List[str] = [
            "LEFT/RIGHT: Move",
            "SPACE: Jump",
            "ESC: Return to Title"
        ]
        for i, control in enumerate(controls):
            control_text: pygame.Surface = control_font.render(
                control, True, Config.COLOR_BLACK)
            control_rect: pygame.Rect = control_text.get_rect(
                center=(Config.SCREEN_WIDTH // 2, 450 + i * 35))
            surface.blit(control_text, control_rect)


class GameScene(Scene):
    """ゲーム本編シーン"""
    
    def __init__(self) -> None:
        """ゲーム本編シーンの初期化"""
        self.player: Player = Player()
        self.blocks: List[Block] = self._create_stage()
        self.goal: Goal = Goal()
        self.camera_x: int = 0  # カメラの X 座標（ワールド座標）
        self.score: int = 0
        self.font: pygame.font.Font = pygame.font.Font(None, 36)
    
        # 制限時間タイマーのセット
        self.time_remaining: float = Config.TIME_LIMIT
        
        # 道中の通常ザコ敵のみ（テスト用に目の前に配置）
        self.enemies: List[Enemy] = [
            Enemy(500, 300),
            Enemy(1200, 200),
            Enemy(2000, 300)
        ]
        
        # ボスをゴール手前に配置（テスト用に目の前に配置）
        self.boss: Optional[Boss] = Boss(2860, 200)
        
    def _create_stage(self) -> List[Block]:
        """ステージを作成（拡張版）"""
        blocks: List[Block] = []
        
        # 第1セクション：初期エリア（X=0~400）
        for i in range(7):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        
        # 上昇する足場
        blocks.append(Block(300, 420))
        blocks.append(Block(350, 380))
        blocks.append(Block(400, 340))
        
        # 第2セクション：中盤エリア（X=400~1000）
        for i in range(7, 15):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        
        # 連続した浮き足場（壊れた橋風）
        for i in range(6):
            if i % 2 == 0:
                blocks.append(Block(450 + i * 100, 380))
        
        # 階段状の足場
        for i in range(4):
            blocks.append(Block(850 + i * Config.BLOCK_WIDTH, 450 - i * Config.BLOCK_HEIGHT))
        
        # 第3セクション：中盤後期（X=1000~1600）
        blocks.append(Block(1100, 350))
        blocks.append(Block(1200, 350))
        blocks.append(Block(1300, 300))
        blocks.append(Block(1400, 300))
        blocks.append(Block(1500, 250))
        blocks.append(Block(1600, 250))
        
        # 地面に戻る坂
        for i in range(3):
            blocks.append(Block(1700 + i * Config.BLOCK_WIDTH, 450 + i * Config.BLOCK_HEIGHT // 2))
        
        # 第4セクション：後半エリア（X=1900~2400）
        for i in range(20, 27):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        
        # 複雑な浮き足場パターン
        blocks.append(Block(2000, 400))
        blocks.append(Block(2100, 350))
        blocks.append(Block(2150, 350))
        blocks.append(Block(2200, 300))
        blocks.append(Block(2250, 300))
        blocks.append(Block(2300, 350))
        blocks.append(Block(2350, 350))
        blocks.append(Block(2400, 400))
        
        # 第5セクション：最終エリア（X=2400~3100）
        for i in range(27, 35):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        
        # ゴール手前の上昇足場
        blocks.append(Block(2600, 420))
        blocks.append(Block(2700, 380))
        blocks.append(Block(2800, 350))
        
        # ゴール直前の着地足場
        blocks.append(Block(2900, 350))
        
        return blocks
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        """イベント処理（シーン切り替え判定）"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return
    
    def update(self) -> Optional[SceneType]:
        """ゲーム状態の更新"""
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        if keys[pygame.K_ESCAPE]:
            return SceneType.TITLE
        
        # 制限時間のカウントダウン
        self.time_remaining -= 1 / Config.FPS
        if self.time_remaining <= 0:
            self.time_remaining = 0
            return SceneType.GAME_OVER
        
        self.player.update(self.blocks)
        player_rect = self.player.get_rect()
        
        # --- ① 通常ザコ敵のループ（衝突＆画面外消滅処理） ---
        enemies_to_remove = []
        for enemy in self.enemies:
            enemy.update(self.blocks)
            
            # カメラの左外に完全に見えなくなったら消滅
            if enemy.x + enemy.width < self.camera_x:
                enemies_to_remove.append(enemy)
                continue
            
            # 通常敵との衝突判定
            if player_rect.colliderect(enemy.get_rect()):
                if player_rect.bottom <= enemy.get_rect().top + 15 and self.player.vy >= 0:
                    self.player.vy = -Config.PLAYER_JUMP_POWER * 0.8
                    enemies_to_remove.append(enemy)
                    self.score += 100
                else:
                    return SceneType.GAME_OVER
                    
        for enemy in enemies_to_remove:
            self.enemies.remove(enemy)
            
        # --- ② ボスの計算と衝突処理 ---
        if self.boss is not None:
            self.boss.update(self.blocks)
            if player_rect.colliderect(self.boss.get_rect()):
                if player_rect.bottom <= self.boss.get_rect().top + 20 and self.player.vy >= 0:
                    self.player.vy = -Config.PLAYER_JUMP_POWER * 1.0  # ボスを踏むと大ジャンプ
                    if self.boss.take_damage():
                        self.boss = None
                        self.score += 1000
                else:
                    return SceneType.GAME_OVER
        
        self._update_camera()
        
        if self.goal.check_collision(self.player.get_rect()): 
            return SceneType.GAME_CLEAR
        if self.player.y > Config.SCREEN_HEIGHT + 100: 
            return SceneType.GAME_OVER
            
        return None

    def _update_camera(self) -> None:
        """カメラの位置を更新（プレイヤーを追従）"""
        target_camera_x: int = int(self.player.x) - Config.SCREEN_WIDTH // 4
        max_camera_x: int = Config.STAGE_MAX_X - Config.SCREEN_WIDTH
        
        if target_camera_x < 0:
            self.camera_x = 0
        elif target_camera_x > max_camera_x:
            self.camera_x = max_camera_x
        else:
            self.camera_x = target_camera_x
    
    def draw(self, surface: pygame.Surface) -> None:
        """ゲーム画面の描画"""
        # 背景を描画
        surface.fill(Config.COLOR_LIGHT_BLUE)
        
        # ブロックを描画
        for block in self.blocks:
            block.draw(surface, self.camera_x)
        
        # ゴールを描画
        self.goal.draw(surface, self.camera_x)
        
        # --- 通常ザコ敵の描画 ---
        for enemy in self.enemies: 
            enemy.draw(surface, self.camera_x)
            
        # --- ボスの描画と残りHP表示 ---
        if self.boss is not None:
            self.boss.draw(surface, self.camera_x)
            boss_screen_x = int(self.boss.x) - self.camera_x
            hp_text = self.font.render("HP: " + "★" * self.boss.hp, True, Config.COLOR_RED)
            surface.blit(hp_text, (boss_screen_x, int(self.boss.y) - 30))
        
        # プレイヤーを描画
        self.player.draw(surface, self.camera_x)
        
        # 情報UI（タイムとスコア、座標）の描画
        seconds = max(0, int(self.time_remaining))
        score_text = self.font.render(f"Score: {self.score} | TIME: {seconds} | X: {int(self.player.x)}", True, Config.COLOR_BLACK)
        surface.blit(score_text, (10, 10))
        
        # 操作ヒント
        hint_font: pygame.font.Font = pygame.font.Font(None, 20)
        hint_text: pygame.Surface = hint_font.render("ESC: Back to Title", True, Config.COLOR_BLACK)
        surface.blit(hint_text, (Config.SCREEN_WIDTH - 200, 10))

class GameClearScene(Scene):
    """ゲームクリア画面シーン"""
    
    def __init__(self) -> None:
        """ゲームクリア画面の初期化"""
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        """
        イベント処理
        
        Args:
            event: pygame のイベントオブジェクト
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # スペースキーでタイトルに戻る
                return
    
    def update(self) -> Optional[SceneType]:
        """
        更新処理
        
        Returns:
            スペースキーでタイトルシーンに切り替え
        """
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        
        if keys[pygame.K_SPACE]:
            return SceneType.TITLE
        
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        画面描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        # 背景を描画
        surface.fill(Config.COLOR_LIGHT_BLUE)
        
        # ゲームクリアテキストを描画
        clear_text: pygame.Surface = self.title_font.render(
            "GAME CLEAR!", True, Config.COLOR_GREEN)
        clear_rect: pygame.Rect = clear_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 150))
        surface.blit(clear_text, clear_rect)
        
        # 説明テキストを描画
        instruction_text: pygame.Surface = self.instruction_font.render(
            "Congratulations!", True, Config.COLOR_BLACK)
        instruction_rect: pygame.Rect = instruction_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 300))
        surface.blit(instruction_text, instruction_rect)
        
        # 続行指示を描画
        continue_font: pygame.font.Font = pygame.font.Font(None, 40)
        continue_text: pygame.Surface = continue_font.render(
            "Press SPACE to Back to Title", True, Config.COLOR_BLACK)
        continue_rect: pygame.Rect = continue_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 450))
        surface.blit(continue_text, continue_rect)


class GameOverScene(Scene):
    """ゲームオーバー画面シーン"""
    
    def __init__(self) -> None:
        """ゲームオーバー画面の初期化"""
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
        self.countdown: int = 0  # 自動リセットまでのカウント
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        """
        イベント処理
        
        Args:
            event: pygame のイベントオブジェクト
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # スペースキーでリトライ
                return
            elif event.key == pygame.K_ESCAPE:
                # ESCキーでタイトルに戻る
                return
    
    def update(self) -> Optional[SceneType]:
        """
        更新処理
        
        Returns:
            スペースキーでゲーム再開、ESCキーでタイトルに戻る
        """
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        
        if keys[pygame.K_SPACE]:
            return SceneType.GAME
        elif keys[pygame.K_ESCAPE]:
            return SceneType.TITLE
        
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        画面描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        # 背景を描画
        surface.fill(Config.COLOR_BLACK)
        
        # ゲームオーバーテキストを描画
        game_over_text: pygame.Surface = self.title_font.render(
            "GAME OVER", True, Config.COLOR_RED)
        game_over_rect: pygame.Rect = game_over_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 200))
        surface.blit(game_over_text, game_over_rect)
        
        # 説明テキストを描画
        instruction_text: pygame.Surface = self.instruction_font.render(
            "Press SPACE to Retry", True, Config.COLOR_WHITE)
        instruction_rect: pygame.Rect = instruction_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 350))
        surface.blit(instruction_text, instruction_rect)
        
        # タイトルに戻るオプションを表示
        back_font: pygame.font.Font = pygame.font.Font(None, 30)
        back_text: pygame.Surface = back_font.render(
            "Press ESC to Back to Title", True, Config.COLOR_WHITE)
        back_rect: pygame.Rect = back_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 450))
        surface.blit(back_text, back_rect)


# ================== ゲームメインクラス ==================

class Game:
    """
    ゲーム全体を管理するメインクラス
    
    メインループ、シーン管理、入力処理、描画を統括します。
    """
    
    def __init__(self) -> None:
        """ゲームの初期化"""
        # Pygame の初期化
        pygame.init()
        
        # ディスプレイの設定
        self.surface: pygame.Surface = pygame.display.set_mode(
            (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption("Fake Mario - 2D Platformer")
        
        # クロックの設定（FPS制御用）
        self.clock: pygame.time.Clock = pygame.time.Clock()
        
        # シーン管理
        self.current_scene_type: SceneType = SceneType.TITLE
        self.scenes: dict = {
            SceneType.TITLE: TitleScene(),
            SceneType.GAME: GameScene(),
            SceneType.GAME_OVER: GameOverScene(),
            SceneType.GAME_CLEAR: GameClearScene()
        }
        
        self.running: bool = True
    
    def get_current_scene(self) -> Scene:
        """
        現在のシーンを取得
        
        Returns:
            現在のシーンオブジェクト
        """
        return self.scenes[self.current_scene_type]
    
    def handle_events(self) -> None:
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # ウィンドウが閉じられた
                self.running = False
            else:
                # 現在のシーンにイベントを渡す
                self.get_current_scene().handle_input(event)
    
    def update(self) -> None:
        """ゲーム状態の更新"""
        current_scene: Scene = self.get_current_scene()
        next_scene_type: Optional[SceneType] = current_scene.update()
        
        # シーンの切り替え
        if next_scene_type is not None:
            self.current_scene_type = next_scene_type
            # シーン切り替え時に新しいインスタンスを作成（状態をリセット）
            if self.current_scene_type == SceneType.GAME:
                self.scenes[SceneType.GAME] = GameScene()
            elif self.current_scene_type == SceneType.GAME_OVER:
                self.scenes[SceneType.GAME_OVER] = GameOverScene()
            elif self.current_scene_type == SceneType.GAME_CLEAR:
                self.scenes[SceneType.GAME_CLEAR] = GameClearScene()
    
    def draw(self) -> None:
        """画面描画"""
        # 現在のシーンを描画
        self.get_current_scene().draw(self.surface)
        
        # 画面更新
        pygame.display.flip()
    
    def run(self) -> None:
        """
        ゲームのメインループを実行
        
        このメソッドがゲーム終了まで実行されます。
        """
        while self.running:
            # イベント処理
            self.handle_events()
            
            # 状態更新
            self.update()
            
            # 描画
            self.draw()
            
            # FPS制御
            self.clock.tick(Config.FPS)
        
        # クリーンアップ
        pygame.quit()
        sys.exit()


# ================== エントリーポイント ==================

if __name__ == "__main__":
    """
    ゲーム実行のエントリーポイント
    
    このスクリプトを直接実行することでゲームが起動します。
    """
    game: Game = Game()
    game.run()
