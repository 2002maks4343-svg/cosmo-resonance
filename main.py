"""Точка входа в игру «Космо-Резонанс»."""
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from game import CosmoGame
from ui.menu import MenuScreen
from ui.galaxy_map import GalaxyMapScreen
from ui.shop import ShopScreen
from ui import sound
from save import progress as prog


Window.clearcolor = (0.02, 0.02, 0.06, 1)


class MenuScreenWrapper(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app
        self.menu = None

    def on_enter(self):
        sound.play_music("menu")
        self.clear_widgets()
        self.menu = MenuScreen(
            on_play=self.go_to_map,
            on_shop=self.go_to_shop,
            on_settings=self.settings,
            on_exit=self.exit_app,
        )
        self.add_widget(self.menu)

    def go_to_map(self):
        print("▶ ИГРАТЬ → карта")
        self.manager.current = "map"

    def go_to_shop(self):
        print("🛒 МАГАЗИН")
        self.manager.current = "shop"

    def settings(self):
        print("⚙ НАСТРОЙКИ (заглушка)")

    def exit_app(self):
        print("🚪 ВЫХОД")
        App.get_running_app().stop()


class ShopScreenWrapper(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app
        self.shop = None

    def on_enter(self):
        sound.play_music("menu")
        if self.shop is not None:
            self.remove_widget(self.shop)
        self.shop = ShopScreen(
            app_ref=self.app_ref,
            on_back=self.go_to_menu,
        )
        self.add_widget(self.shop)

    def go_to_menu(self):
        print("⬅ В меню из магазина")
        self.manager.current = "menu"


class MapScreenWrapper(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app
        self.map_screen = None

    def on_enter(self):
        sound.play_music("map")
        if self.map_screen is not None:
            self.remove_widget(self.map_screen)
        self.map_screen = GalaxyMapScreen(
            progress=self.app_ref.progress,
            on_level_selected=self.go_to_game,
            on_back=self.go_to_menu,
        )
        self.add_widget(self.map_screen)

    def go_to_game(self, level_num):
        print(f"▶ Уровень {level_num}")
        self.app_ref.current_level = level_num
        self.manager.current = "game"

    def go_to_menu(self):
        print("⬅ В меню")
        self.manager.current = "menu"


class GameScreenWrapper(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app
        self.game = None

    def on_enter(self):
        sound.play_music("level")
        self._create_game()

    def _create_game(self):
        if self.game is not None:
            self.remove_widget(self.game)
            self.game = None
        print(f"🎬 Создаём игру для уровня {self.app_ref.current_level}")
        self.game = CosmoGame(
            level_num=self.app_ref.current_level,
            on_back_to_menu=self.go_to_menu,
            on_level_complete=self.go_to_map,
            on_next_level=self.go_to_next_level,
        )
        self.add_widget(self.game)

    def go_to_menu(self):
        print("⬅ В меню из игры")
        self.manager.current = "menu"

    def go_to_map(self):
        print("🗺 К карте из игры")
        self.manager.current = "map"

    def go_to_next_level(self):
        next_num = self.app_ref.current_level + 1
        if next_num > 30:
            print("🏆 Это был последний уровень!")
            self.manager.current = "map"
            return
        print(f"➡️ Следующий уровень: {next_num}")
        self.app_ref.current_level = next_num
        self._create_game()


class CosmoApp(App):
    def build(self):
        self.title = "Космо-Резонанс"

        sound.load_all()

        self.progress = prog.load_progress()
        self.current_level = 1

        sm = ScreenManager()
        sm.add_widget(MenuScreenWrapper(self, name="menu"))
        sm.add_widget(ShopScreenWrapper(self, name="shop"))
        sm.add_widget(MapScreenWrapper(self, name="map"))
        sm.add_widget(GameScreenWrapper(self, name="game"))
        sm.current = "menu"
        return sm


if __name__ == "__main__":
    CosmoApp().run()