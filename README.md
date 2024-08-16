# WARZONE-AFK/DERANK-BOT
a simple python afk bot for warzone 

Load the game, unbind the auto move forward key in game settings (h)

open console in main directory of project

type
pip install -r requirements.txt

                  if pyqt5 is being stoopid




 
              pip install PyQt5==5.15.4
              python -m pip install --upgrade pip
              pip install -r requirements.txt


type  
python bot.py


tab back into game,  press and hold h key + 4 key to toggle AFK bot

make sure you are tabbed back into the cod window, the bot is moving and says activated before actually going AFK.

the code is self explainatory. 

It uses opencv to screenshot parts of the screen looking for the "play again" button.

every so often it presses f key , as to skip kill cams, and pickup loots/open crates.
(version 2 uses the F key stroke to trigger screenshot detection for buttons, and can open the game if it crashes and get back into  a match to resume the afk bot )

this is a work in progress, and i stole the entire keyinput.py from a repo i found for mw2019, shoutout whoever made it.
its not detected, its not being picked up in screenshot detection etc.

it will automatically click the play again button, AND the yes button to confirm and auto join the next match.
it automtically disengages the movement macros and is a functioning loop.

the console keeps track of button clicks, and shows when movement is stopped and started, as well as a basic text overlay in game
(have not been detected in 2 weeks for the overlay but who knows)

use at your own risk, if it doesnt work for you, ask chat gpt.

you can change the PNG files , as they are the buttons the ai looks for to press.  if you use color filters etc you should probably re create your own PNG button files, to customize it to your setup  (this is the fix if it doesnt work right out of the gate)


Clicked PLAY AGAIN at position: (2046, 1224)
PLAY AGAIN button still detected, clicking again...
PLAY AGAIN button no longer detected.
Looking for the YES button...
Clicked YES at position: (944, 804)



the positions of the buttons will change with your differing resolutions, manually find your coordinates and replace these numbers in the code 

 (944, 804) yes button
 (2046, 1224) play again button
