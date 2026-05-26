import pygame
import sys
from typing import Tuple, List, Optional, Sequence
from enum import Enum
from abc import ABC, abstractmethod


# ==============================================================================
# 1. 定数・グローバル設定 (Config & Enums)
# ==============================================================================
# ゲーム全体の画面サイズ、色、キャラクターの初期パラメータ、各種状態の定義を一元管理します。

class Config:
    """ゲーム全体の設定値を管理するクラス"""
    
    # 画面・フレームレート設定
    SCREEN_WIDTH: int = 800
    SCREEN_HEIGHT: int = 600
    FPS: int = 60
    
    # 色定義（RGBカラーコード）
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
    
    # プレイヤーの物理・初期配置設定
    PLAYER_WIDTH: int = 32
    PLAYER_HEIGHT: int = 48
    PLAYER_START_X: int = 100
    PLAYER_START_Y: int = 400
    PLAYER_MOVE_SPEED: int = 5
    PLAYER_JUMP_POWER: int = 15
    
    # 世界の物理設定（重力）
    GRAVITY: float = 0.6
    MAX_FALL_SPEED: int = 20
    
    # 設置ブロックの標準サイズ
    BLOCK_WIDTH: int = 64
    BLOCK_HEIGHT: int = 64
    
    # ゴールオブジェクトのサイズと配置座標
    GOAL_WIDTH: int = 50
    GOAL_HEIGHT: int = 80
    GOAL_X: int = 3000  # ゴールのX座標（ワールド座標）
    GOAL_Y: int = 350   # ゴールのY座標（ワールド座標）
    
    # ステージの右端限界値
    STAGE_MAX_X: int = 3100


class SceneType(Enum):
    """ゲームの進行シーンを識別する列挙型"""
    TITLE = 1
    GAME = 2
    GAME_OVER = 3
    GAME_CLEAR = 4


class ItemType(Enum):
    """出現するアイテムの効果を識別する列挙型"""
    GROW = 1        # 巨大化（スーパーキノコ風）
    INVINCIBLE = 2  # 無敵（スター風）
    FIRE = 3        # 攻撃可能（ファイアフラワー風）


class PlayerState(Enum):
    """プレイヤーの現在のパワーアップ形態を識別する列挙型"""
    NORMAL = 1
    BIG = 2
    FIRE = 3


# ==============================================================================
# 2. ゲームオブジェクトクラス群 (Blocks, Goal, Fireball, Items, Enemies)
# ==============================================================================
# ステージを構成する要素、ギミック、飛び道具、敵キャラクターの振る舞いを定義します。

class Block:
    """ステージの床や足場を表すクラス"""
    
    def __init__(self, x: int, y: int, width: int = Config.BLOCK_WIDTH,
                 height: int = Config.BLOCK_HEIGHT, color: Tuple[int, int, int] = Config.COLOR_GREEN) -> None:
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.color: Tuple[int, int, int] = color
    
    def get_rect(self) -> pygame.Rect:
        """衝突判定用のRectオブジェクトを返す"""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """カメラ座標を考慮して画面内にあればブロックを描画する"""
        screen_x: int = self.x - camera_x
        # 画面外なら処理をスキップ（描画負荷削減）
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        
        rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)          # 中身の塗りつぶし
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2) # 輪郭線


class Goal:
    """ステージのゴール（ポール・砦の代わり）を表すクラス"""
    
    def __init__(self, x: int = Config.GOAL_X, y: int = Config.GOAL_Y,
                 width: int = Config.GOAL_WIDTH, height: int = Config.GOAL_HEIGHT) -> None:
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.color: Tuple[int, int, int] = Config.COLOR_GOLD
    
    def get_rect(self) -> pygame.Rect:
        """衝突判定用のRectオブジェクトを返す"""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def check_collision(self, player_rect: pygame.Rect) -> bool:
        """プレイヤーがゴールに触れたかどうかを判定"""
        return player_rect.colliderect(self.get_rect())
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """ゴール本体と、中央の星型装飾（ポリゴン）を描画する"""
        screen_x: int = self.x - camera_x
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        
        goal_rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, goal_rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, goal_rect, 3)
        
        # ゴール中央に描かれる星型の簡易ポリゴンデータ
        center_x: int = screen_x + self.width // 2
        center_y: int = self.y + self.height // 2
        pygame.draw.polygon(surface, Config.COLOR_YELLOW, [
            (center_x, center_y - 8), (center_x + 4, center_y - 2),
            (center_x + 8, center_y), (center_x + 4, center_y + 4),
            (center_x + 6, center_y + 8), (center_x, center_y + 5),
            (center_x - 6, center_y + 8), (center_x - 4, center_y + 4),
            (center_x - 8, center_y), (center_x - 4, center_y - 2)
        ])


class Fireball:
    """ファイア状態のプレイヤーが放つ火の玉クラス"""
    
    def __init__(self, x: float, y: float, facing_right: bool) -> None:
        self.x: float = x
        self.y: float = y
        self.width: int = 16
        self.height: int = 16
        self.vx: float = 8.0 if facing_right else -8.0 # プレイヤーの向きに応じて左右へ射出
        self.vy: float = 0.0
        self.color: Tuple[int, int, int] = (255, 69, 0)
        self.is_alive: bool = True

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self, blocks: List[Block]) -> None:
        """重力を適用し、ブロックと衝突した場合はバウンドか消滅を判定する"""
        self.vy += Config.GRAVITY
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED

        self.x += self.vx
        self.y += self.vy

        fire_rect = self.get_rect()
        
        # ブロックとの当たり判定（床なら上へ弾み、横壁なら消滅）
        for block in blocks:
            block_rect = block.get_rect()
            if fire_rect.colliderect(block_rect):
                overlap_y_from_top = fire_rect.bottom - block_rect.top
                overlap_x_from_left = fire_rect.right - block_rect.left
                overlap_x_from_right = block_rect.right - fire_rect.left
                
                min_overlap = min(overlap_y_from_top, overlap_x_from_left, overlap_x_from_right)
                
                if min_overlap == overlap_y_from_top:
                    self.y = block_rect.top - self.height
                    self.vy = -6.0  # 床にヒットしたため上方にバウンド
                else:
                    self.is_alive = False  # 側面に当たった場合は消滅
                    return

        # 画面外（奈落）またはステージ外に出たらフラグを折る
        if self.y > Config.SCREEN_HEIGHT or self.x < 0 or self.x > Config.STAGE_MAX_X:
            self.is_alive = False

    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """火の玉を楕円（レンズ形）として描画"""
        screen_x: int = int(self.x) - camera_x
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        rect: pygame.Rect = pygame.Rect(screen_x, int(self.y), self.width, self.height)
        pygame.draw.ellipse(surface, self.color, rect)
        pygame.draw.ellipse(surface, Config.COLOR_BLACK, rect, 1)


class Item:
    """ステージ上に配置されるアイテムクラス（静止配置）"""
    
    def __init__(self, x: int, y: int, item_type: ItemType) -> None:
        self.x: int = x
        self.y: int = y
        self.width: int = 32
        self.height: int = 32
        self.item_type: ItemType = item_type
        
        # アイテムの種類に応じたシンボルカラーの設定
        if self.item_type == ItemType.GROW:
            self.color: Tuple[int, int, int] = (255, 100, 100)   # 赤（キノコ）
        elif self.item_type == ItemType.INVINCIBLE:
            self.color: Tuple[int, int, int] = Config.COLOR_GOLD # 金（スター）
        elif self.item_type == ItemType.FIRE:
            self.color: Tuple[int, int, int] = (255, 140, 0)     # オレンジ（フラワー）

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """アイテムボックス風の矩形と内枠を描画"""
        screen_x: int = self.x - camera_x
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return

        rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)
        
        # 内側の装飾用白枠
        inner: pygame.Rect = pygame.Rect(screen_x + 8, self.y + 8, self.width - 16, self.height - 16)
        pygame.draw.rect(surface, Config.COLOR_WHITE, inner, 1)


class Enemy:
    """ステージを自動巡回する敵キャラクター（クリボー風）のクラス"""
    
    def __init__(self, x: int, y: int) -> None:
        self.x: float = x
        self.y: float = y
        self.width: int = 32
        self.height: int = 32
        self.vx: float = -2.0  # 最初は左に向かって歩く
        self.vy: float = 0.0
        self.color: Tuple[int, int, int] = (139, 69, 19)  # 茶色
        self.is_alive: bool = True

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self, blocks: List[Block]) -> None:
        """重力移動と、ブロックに衝突した際に向きを反転する巡回AIロジック"""
        self.vy += Config.GRAVITY
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED

        self.x += self.vx
        self.y += self.vy

        enemy_rect = self.get_rect()
        
        # 壁や床との衝突検知
        for block in blocks:
            block_rect = block.get_rect()
            if enemy_rect.colliderect(block_rect):
                overlap_y = enemy_rect.bottom - block_rect.top
                overlap_x_left = enemy_rect.right - block_rect.left
                overlap_x_right = block_rect.right - enemy_rect.left
                
                min_overlap = min(overlap_y, overlap_x_left, overlap_x_right)
                
                if min_overlap == overlap_y:
                    self.y = block_rect.top - self.height
                    self.vy = 0.0  # 接地
                elif min_overlap == overlap_x_left:
                    self.x = block_rect.left - self.width
                    self.vx *= -1  # 左の壁にぶつかったので右へ反転
                elif min_overlap == overlap_x_right:
                    self.x = block_rect.right
                    self.vx *= -1  # 右の壁にぶつかったので左へ反転

        # 崖から落ちて画面外に行ったら消滅フラグを立てる
        if self.y > Config.SCREEN_HEIGHT + 100:
            self.is_alive = False

    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """敵本体と、怒っているような目元（直線）を描画"""
        screen_x: int = int(self.x) - camera_x
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
            
        rect: pygame.Rect = pygame.Rect(screen_x, int(self.y), self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)
        
        # 簡易的な怒り目の描画
        eye_y = int(self.y) + 8
        pygame.draw.line(surface, Config.COLOR_BLACK, (screen_x + 6, eye_y), (screen_x + 12, eye_y + 4), 2)
        pygame.draw.line(surface, Config.COLOR_BLACK, (screen_x + 26, eye_y), (screen_x + 20, eye_y + 4), 2)


# ==============================================================================
# 3. プレイヤークラス (Player)
# ==============================================================================
# 操作、物理（移動・ジャンプ）、パワーアップ状態に応じたサイズ変更や攻撃処理、ダメージ処理を担当します。

class Player:
    """プレイヤーキャラクターを制御するメインクラス"""
    
    def __init__(self, x: int = Config.PLAYER_START_X,
                 y: int = Config.PLAYER_START_Y,
                 width: int = Config.PLAYER_WIDTH,
                 height: int = Config.PLAYER_HEIGHT) -> None:
        self.x: float = x
        self.y: float = y
        self.width: int = width
        self.height: int = height
        
        self.vx: float = 0.0
        self.vy: float = 0.0
        
        self.is_jumping: bool = False
        self.is_on_ground: bool = True
        self.color: Tuple[int, int, int] = Config.COLOR_BLUE
        self.facing_right: bool = True
        
        # 特殊状態・タイマー関連
        self.state: PlayerState = PlayerState.NORMAL
        self.is_invincible: bool = False      # スター無敵フラグ
        self.invincible_timer: int = 0         # スター無敵の持続フレーム
        self.damage_invincible_timer: int = 0  # ダメージ後の被弾点滅無敵フレーム
        self.fire_cooldown: int = 0           # 連射制限用クールダウン
        self.pending_fireballs: List[Fireball] = []  # 生成された火の玉をシーンへ渡すための一時リスト
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(int(self.y)), self.width, self.height)
    
    def change_state(self, new_state: PlayerState) -> None:
        """変身処理：状態（NORMAL / BIG / FIRE）に応じてサイズとカラーを変更する"""
        old_height = self.height
        self.state = new_state
        
        if self.state == PlayerState.NORMAL:
            self.height = Config.PLAYER_HEIGHT
            self.color = Config.COLOR_BLUE
        elif self.state == PlayerState.BIG:
            self.height = int(Config.PLAYER_HEIGHT * 1.4)  # 通常の1.4倍の高さ
            self.color = (0, 150, 255)
        elif self.state == PlayerState.FIRE:
            self.height = int(Config.PLAYER_HEIGHT * 1.4)
            self.color = Config.COLOR_RED  # ファイア状態は赤
            
        # サイズ変化時に地面にめり込んだり浮いたりする座標のギャップを補正
        self.y -= (self.height - old_height)

    def hit_enemy(self) -> Optional[SceneType]:
        """敵に接触した際の被ダメージ処理（変身段階の格下げ、またはゲームオーバー判定）"""
        # 各種無敵時間中ならダメージを受けない
        if self.is_invincible or self.damage_invincible_timer > 0:
            return None
            
        if self.state == PlayerState.FIRE:
            self.change_state(PlayerState.BIG)   # ファイアから大きいに格下げ
            self.damage_invincible_timer = 60
        elif self.state == PlayerState.BIG:
            self.change_state(PlayerState.NORMAL) # 大きいから通常に格下げ
            self.damage_invincible_timer = 60
        else:
            # 通常状態で被弾した場合はゲームオーバーをシーンマネージャーへ通知
            return SceneType.GAME_OVER
        return None

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """キーボード入力を読み取り、左右移動、ジャンプ、火の玉発射を制御"""
        # 左右の移動入力
        if keys[pygame.K_LEFT]:
            self.vx = -Config.PLAYER_MOVE_SPEED
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vx = Config.PLAYER_MOVE_SPEED
            self.facing_right = True
        else:
            self.vx = 0.0
        
        # ジャンプ入力（接地時のみ有効）
        if keys[pygame.K_SPACE] and self.is_on_ground:
            self.vy = -Config.PLAYER_JUMP_POWER
            self.is_jumping = True
            self.is_on_ground = False
            
        # ファイア弾射出入力（Xキー）
        if keys[pygame.K_x] and self.state == PlayerState.FIRE and self.fire_cooldown == 0:
            fx = self.x + self.width if self.facing_right else self.x - 16
            fy = self.y + self.height // 3
            self.pending_fireballs.append(Fireball(fx, fy, self.facing_right))
            self.fire_cooldown = 15  # 15フレーム（0.25秒）の硬直時間を設定


    def apply_gravity(self) -> None:
        """プレイヤーに重力を加算する"""
        self.vy += Config.GRAVITY
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED
    
    def update(self, blocks: List[Block]) -> None:
        """各種タイマー減算、位置更新、ブロックとの衝突補正、奈落への落下リセット処理"""
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.is_invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.is_invincible = False
        if self.damage_invincible_timer > 0:
            self.damage_invincible_timer -= 1

        self.apply_gravity()
        
        self.x += self.vx
        self.y += self.vy
        
        self.is_on_ground = False
        self._check_block_collisions(blocks)
        
        # 画面外（奈落）へ落ちた際、プレイヤー状態を初期値に戻す
        if self.y > Config.SCREEN_HEIGHT + 100:
            self.reset()
    
    def _check_block_collisions(self, blocks: List[Block]) -> None:
        """地形ブロック群とのAABB（矩形）衝突判定と、4方向のめり込み押し戻し補正"""
        player_rect: pygame.Rect = self.get_rect()
        
        for block in blocks:
            block_rect: pygame.Rect = block.get_rect()
            if not player_rect.colliderect(block_rect):
                continue
            
            # 各方向の重なり具合を計算
            overlap_y_from_top: int = player_rect.bottom - block_rect.top
            overlap_y_from_bottom: int = block_rect.bottom - player_rect.top
            overlap_x_from_left: int = player_rect.right - block_rect.left
            overlap_x_from_right: int = block_rect.right - player_rect.left
            
            min_overlap: int = min(overlap_y_from_top, overlap_y_from_bottom,
                                   overlap_x_from_left, overlap_x_from_right)
            
            # 最も浅い侵入方向を割り出し、その方向と逆へ押し戻す
            if min_overlap == overlap_y_from_top:
                self.y = block_rect.top - self.height
                self.vy = 0.0
                self.is_on_ground = True
                self.is_jumping = False
            elif min_overlap == overlap_y_from_bottom:
                self.y = block_rect.bottom
                self.vy = 0.0
            elif min_overlap == overlap_x_from_left:
                self.x = block_rect.left - self.width
            elif min_overlap == overlap_x_from_right:
                self.x = block_rect.right
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """プレイヤー描画。ダメージ点滅、スター点滅、向きに応じた目の描画を行う"""
        # 被弾後の無敵時間中は1フレームおきに描画をスキップして点滅を表現
        if self.damage_invincible_timer > 0 and (pygame.time.get_ticks() // 30) % 2 == 0:
            return
            
        screen_x: int = int(self.x) - camera_x
        screen_y: int = int(self.y)
        
        # スター（無敵）状態時は金色に高速点滅
        if self.is_invincible and (pygame.time.get_ticks() // 100) % 2 == 0:
            draw_color = Config.COLOR_GOLD
        else:
            draw_color = self.color
        
        rect: pygame.Rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        pygame.draw.rect(surface, draw_color, rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)
        
        # 進行方向（左右）に合わせて目（丸点）の位置をオフセット調整
        eye_offset: int = 8 if self.facing_right else (self.width - 14)
        pygame.draw.circle(surface, Config.COLOR_BLACK, 
                           (screen_x + eye_offset, screen_y + 12), 2)
    
    def reset(self) -> None:
        """ミス時や初期化時にすべてのステータスをデフォルト状態へリセット"""
        self.x = Config.PLAYER_START_X
        self.y = Config.PLAYER_START_Y
        self.vx = 0.0
        self.vy = 0.0
        self.is_jumping = False
        self.is_on_ground = True
        
        self.change_state(PlayerState.NORMAL)
        self.is_invincible = False
        self.invincible_timer = 0
        self.damage_invincible_timer = 0
        self.fire_cooldown = 0
        self.pending_fireballs = []


# ==============================================================================
# 4. シーン管理システム (Scene, Title, Game, Clear, GameOver)
# ==============================================================================
# 抽象クラス「Scene」をベースに、各ゲーム状態の入力・更新・描画ロジックをカプセル化します。

class Scene(ABC):
    """すべてのシーンの基底となる抽象クラス"""
    @abstractmethod
    def handle_input(self, event: pygame.event.EventType) -> None:
        pass
    
    @abstractmethod
    def update(self) -> Optional[SceneType]:
        pass
    
    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        pass


class TitleScene(Scene):
    """タイトル画面シーン"""
    
    def __init__(self) -> None:
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                return
    
    def update(self) -> Optional[SceneType]:
        # スペースキーが押されたら本編（GAME）シーンへ遷移指示
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            return SceneType.GAME
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(Config.COLOR_LIGHT_BLUE)
        
        # タイトルテキスト表示
        title_text: pygame.Surface = self.title_font.render("FAKE MARIO", True, Config.COLOR_BLACK)
        title_rect: pygame.Rect = title_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 150))
        surface.blit(title_text, title_rect)
        
        # スタート案内テキスト表示
        instruction_text: pygame.Surface = self.instruction_font.render("Press SPACE to Start", True, Config.COLOR_BLACK)
        instruction_rect: pygame.Rect = instruction_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 350))
        surface.blit(instruction_text, instruction_rect)
        
        # 操作説明の一覧表示
        control_font: pygame.font.Font = pygame.font.Font(None, 30)
        controls: List[str] = [
            "LEFT/RIGHT: Move",
            "SPACE: Jump",
            "X: Shoot Fireball (Fire State)",
            "ESC: Return to Title"
        ]
        for i, control in enumerate(controls):
            control_text: pygame.Surface = control_font.render(control, True, Config.COLOR_BLACK)
            control_rect: pygame.Rect = control_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 430 + i * 35))
            surface.blit(control_text, control_rect)


class GameScene(Scene):
    """ゲーム本編（ステージ攻略）シーン"""
    
    def __init__(self) -> None:
        self.player: Player = Player()
        self.blocks: List[Block] = self._create_stage()
        self.goal: Goal = Goal()
        self.camera_x: int = 0
        self.score: int = 0
        self.font: pygame.font.Font = pygame.font.Font(None, 36)
        
        # アクティブな各種ゲームオブジェクト群の動的リスト
        self.items: List[Item] = self._create_items()
        self.fireballs: List[Fireball] = []
        self.enemies: List[Enemy] = self._create_enemies()
    
    def _create_items(self) -> List[Item]:
        """ステージ内の特定ワールド座標にアイテムを配置"""
        items: List[Item] = []
        items.append(Item(350, 330, ItemType.GROW))
        items.append(Item(750, 330, ItemType.INVINCIBLE))
        items.append(Item(2150, 250, ItemType.FIRE))
        return items

    def _create_enemies(self) -> List[Enemy]:
        """ステージ内の特定ワールド座標に敵を配置"""
        enemies: List[Enemy] = []
        enemies.append(Enemy(500, 500 - 32))
        return enemies

    def _create_stage(self) -> List[Block]:
        """起伏や穴のある広大な横スクロールステージをブロックデータとして構築"""
        blocks: List[Block] = []
        # 第1セクション：初期エリア
        for i in range(7):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        blocks.append(Block(300, 420))
        blocks.append(Block(350, 380))
        blocks.append(Block(400, 340))
        
        # 第2セクション：中盤エリア
        for i in range(7, 15):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        for i in range(6):
            if i % 2 == 0:
                blocks.append(Block(450 + i * 100, 380))
        for i in range(4):
            blocks.append(Block(850 + i * Config.BLOCK_WIDTH, 450 - i * Config.BLOCK_HEIGHT))
        
        # 第3セクション
        blocks.append(Block(1100, 350))
        blocks.append(Block(1200, 350))
        blocks.append(Block(1300, 300))
        blocks.append(Block(1400, 300))
        blocks.append(Block(1500, 250))
        blocks.append(Block(1600, 250))
        for i in range(3):
            blocks.append(Block(1700 + i * Config.BLOCK_WIDTH, 450 + i * Config.BLOCK_HEIGHT // 2))
        
        # 第4セクション
        for i in range(20, 27):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        blocks.append(Block(2000, 400))
        blocks.append(Block(2100, 350))
        blocks.append(Block(2150, 350))
        blocks.append(Block(2200, 300))
        blocks.append(Block(2250, 300))
        blocks.append(Block(2300, 350))
        blocks.append(Block(2350, 350))
        blocks.append(Block(2400, 400))
        
        # 第5セクション（ゴール手前）
        for i in range(27, 35):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        blocks.append(Block(2600, 420))
        blocks.append(Block(2700, 380))
        blocks.append(Block(2800, 350))
        blocks.append(Block(2900, 350))
        
        return blocks
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return
    
    def update(self) -> Optional[SceneType]:
        """全オブジェクトの同期更新、及びプレイヤー・火の玉・敵・アイテム間の相互衝突検知"""
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        # ESCキーが押されたら即座にタイトルへ戻る
        if keys[pygame.K_ESCAPE]:
            return SceneType.TITLE
        
        self.player.update(self.blocks)
        
        # プレイヤーが発射した保留中の火の玉オブジェクトをシーンのメインリストへ移管
        if self.player.pending_fireballs:
            self.fireballs.extend(self.player.pending_fireballs)
            self.player.pending_fireballs.clear()
            
        # 火の玉の位置更新と消滅した弾のクリーンアップ
        for fireball in self.fireballs[:]:
            fireball.update(self.blocks)
            if not fireball.is_alive:
                self.fireballs.remove(fireball)
                
        # 敵の位置更新と消滅した敵のクリーンアップ
        for enemy in self.enemies[:]:
            enemy.update(self.blocks)
            if not enemy.is_alive:
                self.enemies.remove(enemy)

        # 衝突判定：【火の玉】 vs 【敵】
        for fireball in self.fireballs[:]:
            for enemy in self.enemies[:]:
                if fireball.get_rect().colliderect(enemy.get_rect()):
                    fireball.is_alive = False
                    enemy.is_alive = False
                    if fireball in self.fireballs:
                        self.fireballs.remove(fireball)
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                    self.score += 100  # 撃破ボーナス
                    break

        # 衝突判定：【プレイヤー】 vs 【敵】
        player_rect = self.player.get_rect()
        for enemy in self.enemies[:]:
            if player_rect.colliderect(enemy.get_rect()):
                # 無敵（スター）状態なら一方的に消滅させる
                if self.player.is_invincible:
                    enemy.is_alive = False
                    self.enemies.remove(enemy)
                    self.score += 100
                    continue
                
                # 上から踏みつけた場合（落下速度がプラスかつ底面が敵の頭上付近）
                if self.player.vy > 0 and (player_rect.bottom - enemy.get_rect().top) < 20:
                    enemy.is_alive = False
                    self.enemies.remove(enemy)
                    self.player.vy = -8.0  # 反動で少し高く跳ね上がる
                    self.score += 100
                else:
                    # 側面、または下から衝突した場合は被弾ダメージ処理を行う
                    damage_result = self.player.hit_enemy()
                    if damage_result == SceneType.GAME_OVER:
                        return SceneType.GAME_OVER

        # 衝突判定：【プレイヤー】 vs 【アイテム】
        for item in self.items[:]:
            if player_rect.colliderect(item.get_rect()):
                if item.item_type == ItemType.GROW:
                    self.player.change_state(PlayerState.BIG)
                elif item.item_type == ItemType.INVINCIBLE:
                    self.player.is_invincible = True
                    self.player.invincible_timer = 300  # 5秒間 (60fps × 5)
                elif item.item_type == ItemType.FIRE:
                    self.player.change_state(PlayerState.FIRE)
                
                self.items.remove(item)
                self.score += 200  # アイテム取得ボーナス
        
        # プレイヤー追従型スクロールカメラの更新
        self._update_camera()
        
        # ゴール到達チェック
        if self.goal.check_collision(self.player.get_rect()):
            return SceneType.GAME_CLEAR
        
        # 画面下部（底）に落ちたら即ゲームオーバーシーンへ
        if self.player.y > Config.SCREEN_HEIGHT + 100:
            return SceneType.GAME_OVER
        
        return None
    
    def _update_camera(self) -> None:
        """プレイヤーの位置に基づいて横スクロールのカメラ位置（オフセット量）を算出"""
        target_camera_x: int = int(self.player.x) - Config.SCREEN_WIDTH // 4
        max_camera_x: int = Config.STAGE_MAX_X - Config.SCREEN_WIDTH
        
        # 左端限界、および右端限界のストッパー処理
        if target_camera_x < 0:
            self.camera_x = 0
        elif target_camera_x > max_camera_x:
            self.camera_x = max_camera_x
        else:
            self.camera_x = target_camera_x
    
    def draw(self, surface: pygame.Surface) -> None:
        """背景塗りつぶし、およびカメラ位置を差し引いた全要素のレイヤー順描画"""
        surface.fill(Config.COLOR_LIGHT_BLUE) # 背景（青空）
        
        # 地形・動的オブジェクトの描画
        for block in self.blocks:
            block.draw(surface, self.camera_x)
            
        for item in self.items:
            item.draw(surface, self.camera_x)
            
        for fireball in self.fireballs:
            fireball.draw(surface, self.camera_x)
            
        for enemy in self.enemies:
            enemy.draw(surface, self.camera_x)
        
        # 固定オブジェクトの描画
        self.goal.draw(surface, self.camera_x)
        self.player.draw(surface, self.camera_x)
        
        # HUD（スコア・座標・状態等の文字情報）の描画
        state_str = self.player.state.name
        if self.player.is_invincible:
            state_str += " + INVINCIBLE"
        score_text: pygame.Surface = self.font.render(
            f"Score: {self.score} | X: {int(self.player.x)} | Status: {state_str}", True, Config.COLOR_BLACK)
        surface.blit(score_text, (10, 10))
        
        # 右上のタイトルバック補助案内テキスト
        hint_font: pygame.font.Font = pygame.font.Font(None, 20)
        hint_text: pygame.Surface = hint_font.render("ESC: Back to Title", True, Config.COLOR_BLACK)
        surface.blit(hint_text, (Config.SCREEN_WIDTH - 150, 10))


class GameClearScene(Scene):
    """ゲームクリア画面シーン"""
    
    def __init__(self) -> None:
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                return
    
    def update(self) -> Optional[SceneType]:
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            return SceneType.TITLE # スペース押下でタイトルシーンへ遷移指示
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(Config.COLOR_LIGHT_BLUE)
        
        clear_text: pygame.Surface = self.title_font.render("GAME CLEAR!", True, Config.COLOR_GREEN)
        clear_rect: pygame.Rect = clear_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 150))
        surface.blit(clear_text, clear_rect)
        
        instruction_text: pygame.Surface = self.instruction_font.render("Congratulations!", True, Config.COLOR_BLACK)
        instruction_rect: pygame.Rect = instruction_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 300))
        surface.blit(instruction_text, instruction_rect)
        
        continue_text: pygame.Surface = self.instruction_font.render("Press SPACE to Back to Title", True, Config.COLOR_BLACK)
        continue_rect: pygame.Rect = continue_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 450))
        surface.blit(continue_text, continue_rect)


class GameOverScene(Scene):
    """ゲームオーバー画面シーン"""
    
    def __init__(self) -> None:
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                return
    
    def update(self) -> Optional[SceneType]:
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            return SceneType.GAME   # スペース押下でリトライ（ゲーム再生成）
        elif keys[pygame.K_ESCAPE]:
            return SceneType.TITLE  # ESC押下でタイトルへ
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(Config.COLOR_BLACK) # ゲームオーバーのみ背景は黒
        
        game_over_text: pygame.Surface = self.title_font.render("GAME OVER", True, Config.COLOR_RED)
        game_over_rect: pygame.Rect = game_over_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 200))
        surface.blit(game_over_text, game_over_rect)
        
        instruction_text: pygame.Surface = self.instruction_font.render("Press SPACE to Retry", True, Config.COLOR_WHITE)
        instruction_rect: pygame.Rect = instruction_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 350))
        surface.blit(instruction_text, instruction_rect)
        
        back_text: pygame.Surface = self.instruction_font.render("Press ESC to Back to Title", True, Config.COLOR_WHITE)
        back_rect: pygame.Rect = back_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 450))
        surface.blit(back_text, back_rect)


# ==============================================================================
# 5. ゲームメインクラス & エントリーポイント (Game & __main__)
# ==============================================================================
# Pygame自体の初期化、メインループの制御、シーンのファクトリおよび切り替え処理を行います。

class Game:
    """ゲームのウィンドウ生成、ループ、イベント、シーンのライフサイクル全般を統括する最上位クラス"""
    
    def __init__(self) -> None:
        pygame.init()
        self.surface: pygame.Surface = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption("Fake Mario - Items Expansion")
        self.clock: pygame.time.Clock = pygame.time.Clock()
        
        # シーン管理ディクショナリの生成と初期シーンの設定
        self.current_scene_type: SceneType = SceneType.TITLE
        self.scenes: dict = {
            SceneType.TITLE: TitleScene(),
            SceneType.GAME: GameScene(),
            SceneType.GAME_OVER: GameOverScene(),
            SceneType.GAME_CLEAR: GameClearScene()
        }
        self.running: bool = True
    
    def get_current_scene(self) -> Scene:
        """現在アクティブなシーンオブジェクトを取得"""
        return self.scenes[self.current_scene_type]
    
    def handle_events(self) -> None:
        """PygameのOSイベント（閉じるボタンなど）を傍受し、各シーンに割り振る"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.get_current_scene().handle_input(event)
    
    def update(self) -> None:
        """現在アクティブなシーンのロジックを更新し、シーンの遷移要求があれば中身を初期化して切り替える"""
        current_scene: Scene = self.get_current_scene()
        next_scene_type: Optional[SceneType] = current_scene.update()
        
        if next_scene_type is not None:
            self.current_scene_type = next_scene_type
            # 状態を引き継がせないため、遷移先のシーンインスタンスを都度新しく初期化して上書きする
            if self.current_scene_type == SceneType.GAME:
                self.scenes[SceneType.GAME] = GameScene()
            elif self.current_scene_type == SceneType.GAME_OVER:
                self.scenes[SceneType.GAME_OVER] = GameOverScene()
            elif self.current_scene_type == SceneType.GAME_CLEAR:
                self.scenes[SceneType.GAME_CLEAR] = GameClearScene()
    
    def draw(self) -> None:
        """現在のシーンの描画関数を呼び出し、ディスプレイをリフレッシュ（フリップ）する"""
        self.get_current_scene().draw(self.surface)
        pygame.display.flip()
    
    def run(self) -> None:
        """メインループ（デルタタイム/FPS固定制御含む）"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(Config.FPS) # 60FPSを維持するようにウェイトを入れる
        
        # ループを抜けたら安全に終了
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    # ゲームインスタンスを生成して実行
    game: Game = Game()
    game.run()