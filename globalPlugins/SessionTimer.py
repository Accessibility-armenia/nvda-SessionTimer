# -*- coding: UTF-8 -*-
import addonHandler
import globalPluginHandler
import gui
import languageHandler
import time
import tones
import ui
import wx

addonHandler.initTranslation()

ADDON_NAME = "Session Timer"
ADDON_VERSION = "0.0.4"
UPDATE_DATE = "2026-03-24"
AUTHOR = "Tigran Navasardyan"

_NVDA_TRANSLATE = _

_TRANSLATIONS = {
	"ru": {
		"Session Timer": "Таймер сеанса",
		"&About Session Timer": "О &Session Timer",
		"About Session Timer": "О Session Timer",
		"Version: {version}": "Версия: {version}",
		"Last updated: {date}": "Последнее обновление: {date}",
		"Author: {author}": "Автор: {author}",
		"This add-on announces how long NVDA has been running.": (
			"Это дополнение сообщает, сколько времени работает NVDA."
		),
		"NVDA has been running for {duration}": "NVDA работает уже {duration}",
		"NVDA started at {time}": "NVDA запущена в {time}",
		"Session timer reset.": "Таймер сеанса сброшен.",
		"{name} version {version}, last updated {date}, author {author}": (
			"{name}, версия {version}, последнее обновление {date}, автор {author}"
		),
		"Announces how long NVDA has been running.": (
			"Сообщает, сколько времени работает NVDA."
		),
		"Announces a short version of the current NVDA session time.": (
			"Сообщает краткую версию текущего времени сеанса NVDA."
		),
		"Announces when NVDA was started.": "Сообщает, когда была запущена NVDA.",
		"Resets the session timer.": "Сбрасывает таймер сеанса.",
		"Announces Session Timer version information.": (
			"Сообщает информацию о версии дополнения Session Timer."
		),
	},
}

_DURATION_LABELS = {
	"en": {
		"hour": ("hour", "hours"),
		"minute": ("minute", "minutes"),
		"second": ("second", "seconds"),
		"short": {
			"hour": "h",
			"minute": "m",
			"second": " S",
		},
	},
	"ru": {
		"hour": ("час", "часа", "часов"),
		"minute": ("минута", "минуты", "минут"),
		"second": ("секунда", "секунды", "секунд"),
		"short": {
			"hour": "ч",
			"minute": "м",
			"second": "с",
		},
	},
}


def _get_language():
	language = languageHandler.getLanguage() or "en"
	if language in _DURATION_LABELS or language in _TRANSLATIONS:
		return language
	baseLanguage = language.split("_")[0]
	if baseLanguage in _DURATION_LABELS or baseLanguage in _TRANSLATIONS:
		return baseLanguage
	return "en"


def _translate(text):
	language = _get_language()
	return _TRANSLATIONS.get(language, {}).get(text, _NVDA_TRANSLATE(text))


def _get_plural_label(value, labels):
	if len(labels) == 2:
		return labels[0] if value == 1 else labels[1]
	mod10 = value % 10
	mod100 = value % 100
	if mod10 == 1 and mod100 != 11:
		return labels[0]
	if mod10 in (2, 3, 4) and mod100 not in (12, 13, 14):
		return labels[1]
	return labels[2]


def _format_duration_part(value, unitName, short=False):
	language = _get_language()
	labels = _DURATION_LABELS.get(language, _DURATION_LABELS["en"])
	if short:
		return f"{value}{labels['short'][unitName]}"
	label = _get_plural_label(value, labels[unitName])
	return f"{value} {label}"


def _format_duration(elapsed, short=False):
	hours, remainder = divmod(int(elapsed), 3600)
	minutes, seconds = divmod(remainder, 60)
	parts = [
		_format_duration_part(hours, "hour", short=short),
		_format_duration_part(minutes, "minute", short=short),
		_format_duration_part(seconds, "second", short=short),
	]
	separator = " " if short else ", "
	return separator.join(parts)


def _build_about_text():
	return "\n".join(
		[
			ADDON_NAME,
			"",
			_translate("Version: {version}").format(version=ADDON_VERSION),
			_translate("Last updated: {date}").format(date=UPDATE_DATE),
			_translate("Author: {author}").format(author=AUTHOR),
			"",
			_translate("This add-on announces how long NVDA has been running."),
		]
	)


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _translate("Session Timer")

	def __init__(self):
		super().__init__()
		self.menuItem = None
		self._resetTimerState()
		self._createMenuItem()

	def terminate(self):
		if self.menuItem is not None:
			toolsMenu = gui.mainFrame.sysTrayIcon.toolsMenu
			menuItemId = self.menuItem.GetId()
			if toolsMenu.FindItemById(menuItemId):
				toolsMenu.Remove(menuItemId)
			self.menuItem = None
		super().terminate()

	def _resetTimerState(self):
		self.startTime = time.time()
		self.startClock = time.strftime("%X")

	def _createMenuItem(self):
		self.menuItem = gui.mainFrame.sysTrayIcon.toolsMenu.Append(
			wx.ID_ANY,
			_translate("&About Session Timer"),
		)
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onAbout, self.menuItem)

	def _announceMessage(self, messageText, tone=800, duration=50):
		tones.beep(tone, duration)
		ui.message(messageText)

	def _getElapsed(self):
		return int(time.time() - self.startTime)

	def onAbout(self, evt):
		gui.messageBox(
			_build_about_text(),
			_translate("About Session Timer"),
			wx.OK | wx.ICON_INFORMATION,
		)

	def script_announceSessionTime(self, gesture):
		durationText = _format_duration(self._getElapsed())
		self._announceMessage(
			_translate("NVDA has been running for {duration}").format(duration=durationText)
		)

	def script_announceShortTime(self, gesture):
		self._announceMessage(_format_duration(self._getElapsed(), short=True))

	def script_announceStartTime(self, gesture):
		self._announceMessage(
			_translate("NVDA started at {time}").format(time=self.startClock)
		)

	def script_resetTimer(self, gesture):
		self._resetTimerState()
		self._announceMessage(_translate("Session timer reset."), tone=600, duration=100)

	def script_announceAddonInfo(self, gesture):
		ui.message(
			_translate("{name} version {version}, last updated {date}, author {author}").format(
				name=ADDON_NAME,
				version=ADDON_VERSION,
				date=UPDATE_DATE,
				author=AUTHOR,
			)
		)

	script_announceSessionTime.__doc__ = _translate(
		"Announces how long NVDA has been running."
	)
	script_announceShortTime.__doc__ = _translate(
		"Announces a short version of the current NVDA session time."
	)
	script_announceStartTime.__doc__ = _translate("Announces when NVDA was started.")
	script_resetTimer.__doc__ = _translate("Resets the session timer.")
	script_announceAddonInfo.__doc__ = _translate(
		"Announces Session Timer version information."
	)

	__gestures = {
		"kb:NVDA+Windows+N": "announceSessionTime",
		"kb:NVDA+Windows+Shift+N": "announceShortTime",
		"kb:NVDA+Windows+Shift+T": "announceStartTime",
		"kb:NVDA+Windows+R": "resetTimer",
		"kb:NVDA+Windows+I": "announceAddonInfo",
	}
