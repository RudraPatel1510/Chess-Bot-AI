import sys
import os
import pygame as p
from chesslogic import GameState, Move
from chessAi import findRandomMoves, findBestMove
from multiprocessing import Process, Queue
import time
import matplotlib.pyplot as plt
import matplotlib.style as style
import matplotlib.patches as mpatches 
from pymongo import MongoClient
from deck import Deck



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUND_DIR = os.path.join(BASE_DIR, "sounds")
IMAGE_DIR = os.path.join(BASE_DIR, "images1")
# Initialize the mixer
p.mixer.init()
# Load sound files
p.mixer.init()
move_sound = p.mixer.Sound(os.path.join(SOUND_DIR, "move-sound.mp3"))
capture_sound = p.mixer.Sound(os.path.join(SOUND_DIR, "capture.mp3"))
promote_sound = p.mixer.Sound(os.path.join(SOUND_DIR, "promote.mp3"))

BOARD_WIDTH = BOARD_HEIGHT = 600
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15  # for animations
IMAGES = {}

SET_WHITE_AS_BOT = False
SET_BLACK_AS_BOT = True



# 1 Green
# LIGHT_SQUARE_COLOR = (237, 238, 209)
# DARK_SQUARE_COLOR = (119, 153, 82)
# MOVE_HIGHLIGHT_COLOR = (84, 115, 161)
# POSSIBLE_MOVE_COLOR = (255, 255, 51)



# 3 Gray
LIGHT_SQUARE_COLOR = (220,220,220)
DARK_SQUARE_COLOR = (170,170,170)
MOVE_HIGHLIGHT_COLOR = (84, 115, 161)
POSSIBLE_MOVE_COLOR = (164,184,196)



move_counter = 1  # Global counter for move number
start_time = time.time()  # Track duration per move
total_moves = 0  # Global variable to track total moves
bot_moves = 0  # Global variable to track bot moves
player_moves = 0  # Global variable to track player moves
bot_durations = []
player_durations = []
bot_win = 0
player_win = 0



def get_game_index():
    if not os.path.exists("game_counter.txt"):
        with open("game_counter.txt", "w") as f:
            f.write("0")
        return 0
    with open("game_counter.txt", "r") as f:
        return int(f.read())

def increment_game_index(current):
    with open("game_counter.txt", "w") as f:
        f.write(str(int(current) + 1))


client = MongoClient("mongodb://localhost:27017/")
db = client["chess_db"]
i = get_game_index()
cn = f"game_{i}"
collection = db[cn]


def save_move(move, is_bot_move):

    global move_counter, start_time

    duration = time.time() - start_time
    # total_duration += duration
    if is_bot_move:
        bot_durations.append(duration)
    else:
        player_durations.append(duration)
    start_time = time.time()  # Reset timer for next move

    move_data = {
        "move_number": move_counter,
        "player": "bot" if is_bot_move else "player",
        "move": str(move),
        # "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M:%S %p"),
        "duration_seconds": round(duration, 2),
        "botwin": bot_win,
        "playerwin": player_win
    }
    move_counter += 1

    # with open("chess_moves.json", "a") as f:
    #     f.write(json.dumps(move_data,indent=4) + "\n")

    collection.insert_one(move_data)


def move_comparision_graph(bot, player):
    if bot == 0 and player == 0:
        print("No moves were made to plot.")
        return 

    try:
        style.use('seaborn-v0_8-v0_8-darkgrid') 
    except:
        plt.grid(True, linestyle='--', linewidth=0.5, axis='y', alpha=0.7)

    categories = ['Player', 'Bot']
    values = [player, bot]
    colors = ['blue', 'red'] 

    # plt.figure(figsize=(8, 6)) 
    bars = plt.bar(categories, values, color=colors)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval, int(yval), va='bottom', ha='center') 

    plt.ylabel('Moves')
    plt.title('Number of Moves per Game')
    plt.ylim(0, max(values) * 1.15) 

    if 'style' not in locals() or not style.library: # Check if styling was applied
        plt.grid(True, linestyle='--', linewidth=0.5, axis='y', alpha=0.7)

    plt.legend(['Player', 'Bot'], loc='upper right')
    plt.show() 


def timepermove_graph(player_durations, bot_durations):

    if not player_durations and not bot_durations:
        print("No duration data provided to plot time per move.")
        return

    try:
        style.use('seaborn-v0_8-darkgrid')
    except:
        plt.grid(True, linestyle='--', linewidth=0.5, axis='both', alpha=0.7)

    legend_handles = [] 

    if player_durations:
        player_move_numbers = range(1, len(player_durations) + 1)
        plt.plot(player_move_numbers, player_durations, marker='o', linestyle='-', color='blue')
        legend_handles.append(mpatches.Patch(color='blue', label='Player'))

    if bot_durations:
        bot_move_numbers = range(1, len(bot_durations) + 1)
        plt.plot(bot_move_numbers, bot_durations, marker='s', linestyle='-', color='red')
        legend_handles.append(mpatches.Patch(color='red', label='Bot'))

    plt.xlabel("Move Number") # X-axis title
    plt.ylabel("Time (seconds)")                  # Y-axis title
    plt.title("Time Taken per Move")              # Plot title

    if 'style' not in locals() or not style.library:
        plt.grid(True, linestyle='--', linewidth=0.5, axis='both', alpha=0.7)

    if legend_handles:
        plt.legend(handles=legend_handles)

    plt.show() 


def loadImages():
    pieces = ['bR', 'bN', 'bB', 'bQ', 'bK',
            'bp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'wp']
    for piece in pieces:
        image_path = os.path.join(IMAGE_DIR, piece + ".png")
        original_image = p.image.load(image_path)
        IMAGES[piece] = p.transform.smoothscale(
            original_image, (SQ_SIZE, SQ_SIZE))


def pawnPromotionPopup(screen, gs):
    font = p.font.SysFont("Times New Roman", 30, False, False)
    text = font.render("Choose promotion:", True, p.Color("black"))

    # Create buttons for promotion choices with images
    button_width, button_height = 100, 100
    buttons = [
        p.Rect(100, 200, button_width, button_height),
        p.Rect(200, 200, button_width, button_height),
        p.Rect(300, 200, button_width, button_height),
        p.Rect(400, 200, button_width, button_height)
    ]

    if gs.whiteToMove:
        button_images = [
            p.transform.smoothscale(p.image.load(
                "images1/bQ.png"), (100, 100)),
            p.transform.smoothscale(p.image.load(
                "images1/bR.png"), (100, 100)),
            p.transform.smoothscale(p.image.load(
                "images1/bB.png"), (100, 100)),
            p.transform.smoothscale(p.image.load("images1/bN.png"), (100, 100))
        ]
    else:
        button_images = [
            p.transform.smoothscale(p.image.load(
                "images1/wQ.png"), (100, 100)),
            p.transform.smoothscale(p.image.load(
                "images1/wR.png"), (100, 100)),
            p.transform.smoothscale(p.image.load(
                "images1/wB.png"), (100, 100)),
            p.transform.smoothscale(p.image.load("images1/wN.png"), (100, 100))
        ]

    while True:
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                mouse_pos = e.pos
                for i, button in enumerate(buttons):
                    if button.collidepoint(mouse_pos):
                        if i == 0:
                            return "Q"  # Return the index of the selected piece
                        elif i == 1:
                            return "R"
                        elif i == 2:
                            return "B"
                        else:
                            return "N"

        screen.fill(p.Color(LIGHT_SQUARE_COLOR))
        screen.blit(text, (110, 150))

        for i, button in enumerate(buttons):
            p.draw.rect(screen, p.Color("white"), button)
            screen.blit(button_images[i], button.topleft)

        p.display.flip()



def main():
    # initialize py game
    global total_moves, bot_moves, player_moves,i, bot_win, player_win
    p.init()
    screen = p.display.set_mode(
        (BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    p.display.set_caption("Chess")
    clock = p.time.Clock()
    screen.fill(p.Color(LIGHT_SQUARE_COLOR))
    moveLogFont = p.font.SysFont("Times New Roman", 12, False, False)
    # Creating gamestate object calling our constructor
    gs = GameState()
    d = Deck()
    d.initialize_deck()
    if (gs.playerWantsToPlayAsBlack):
        gs.board = gs.board1
    validMoves = gs.getValidMoves()
    moveMade = False  
    animate = False  
    loadImages()
    running = True
    squareSelected = ()  # keep tracks of last click
    playerClicks = []
    gameOver = False  # gameover if checkmate or stalemate
    playerWhiteHuman = not SET_WHITE_AS_BOT
    playerBlackHuman = not SET_BLACK_AS_BOT
    AIThinking = False  # True if ai is thinking
    moveFinderProcess = None
    moveUndone = False
    pieceCaptured = False
    positionHistory = ""
    previousPos = ""
    countMovesForDraw = 0
    COUNT_DRAW = 0
    while running:
        humanTurn = (gs.whiteToMove and playerWhiteHuman) or (
            not gs.whiteToMove and playerBlackHuman)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
                if i!=0:
                    increment_game_index(i)  # Increment the game index
                # print(total_moves, bot_moves, player_moves)
                p.quit()
                timepermove_graph(player_durations, bot_durations)
                move_comparision_graph(bot_moves, player_moves)
                # open("chess_moves.json", "w").close()
                total_moves = 0
                bot_moves = 0
                player_moves = 0
                sys.exit()
            # Mouse Handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver:  # allow mouse handling only if its not game over
                    location = p.mouse.get_pos()
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    # if user clicked on same square twice or user click outside board
                    if squareSelected == (row, col) or col >= 8:
                        squareSelected = ()  # deselect
                        playerClicks = []  # clear player clicks
                    else:
                        squareSelected = (row, col)
                        # append player both clicks (place and destination)
                        playerClicks.append(squareSelected)
                    # after second click (at destination)
                    if len(playerClicks) == 2 and humanTurn:
                        # user generated a move
                        move = Move(playerClicks[0], playerClicks[1], gs.board)
                        for i in range(len(validMoves)):
                            # check if the move is in the validMoves
                            if move == validMoves[i]:
                                # Check if a piece is captured at the destination square
                                # print(gs.board[validMoves[i].endRow][validMoves[i].endCol])
                                if gs.board[validMoves[i].endRow][validMoves[i].endCol] != '--':
                                    pieceCaptured = True

                                print(d.draw_card())
                                gs.makeMove(validMoves[i])
                                save_move(str(validMoves[i]), is_bot_move=False)
                                total_moves += 1
                                player_moves += 1
                                if (move.isPawnPromotion):
                                    # Show pawn promotion popup and get the selected piece
                                    promotion_choice = pawnPromotionPopup(
                                        screen, gs)
                                    # Set the promoted piece on the board
                                    gs.board[move.endRow][move.endCol] = move.pieceMoved[0] + \
                                        promotion_choice
                                    promote_sound.play()
                                    pieceCaptured = False
                                # add sound for human move
                                if (pieceCaptured or move.isEnpassantMove):
                                    # Play capture sound
                                    capture_sound.play()
                                    # print("capture sound")
                                elif not move.isPawnPromotion:
                                    # Play move sound
                                    move_sound.play()
                                    # print("move sound")
                                pieceCaptured = False
                                moveMade = True
                                animate = True
                                squareSelected = ()
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [squareSelected]

            # Key Handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_u:  # undo when z is pressed
                    gs.undoMove()
                    # when user undo move valid move change, here we could use [ validMoves = gs.getValidMoves() ] which would update the current validMoves after undo
                    moveMade = True
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()  # terminate the ai thinking if we undo
                        AIThinking = False
                    moveUndone = True
                if e.key == p.K_r:  # reset board when 'r' is pressed
                    gs = GameState()
                    validMoves = gs.getValidMoves()
                    squareSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()  # terminate the ai thinking if we undo
                        AIThinking = False
                    moveUndone = True
                    total_moves = 0
                    bot_moves = 0
                    player_moves = 0

        # AI move finder
        if not gameOver and not humanTurn and not moveUndone:
            if not AIThinking:
                AIThinking = True
                returnQueue = Queue()  # keep track of data, to pass data between threads
                moveFinderProcess = Process(target=findBestMove, args=(
                    gs, validMoves, returnQueue))  # when processing start we call these process
                # call findBestMove(gs, validMoves, returnQueue) #rest of the code could still work even if the ai is thinking
                moveFinderProcess.start()
                # AIMove = findBestMove(gs, validMoves)
                # gs.makeMove(AIMove)
            if not moveFinderProcess.is_alive():
                AIMove = returnQueue.get()  # return from returnQueue
                if AIMove is None:
                    AIMove = findRandomMoves(validMoves)

                if gs.board[AIMove.endRow][AIMove.endCol] != '--':
                    pieceCaptured = True

                print(d.draw_card())
                gs.makeMove(AIMove)
                save_move(str(AIMove), is_bot_move=True)
                total_moves += 1
                bot_moves += 1

                if AIMove.isPawnPromotion:
                    # Show pawn promotion popup and get the selected piece
                    promotion_choice = pawnPromotionPopup(screen, gs)
                    # Set the promoted piece on the board
                    gs.board[AIMove.endRow][AIMove.endCol] = AIMove.pieceMoved[0] + \
                        promotion_choice
                    promote_sound.play()
                    pieceCaptured = False

                # sound for human move
                if (pieceCaptured or AIMove.isEnpassantMove):
                    # Play capture sound
                    capture_sound.play()
                    # print("capture sound")
                elif not AIMove.isPawnPromotion:
                    # Play move sound
                    move_sound.play()
                    # print("move sound")
                pieceCaptured = False
                AIThinking = False
                moveMade = True
                animate = True
                squareSelected = ()
                playerClicks = []

        if moveMade:
            if countMovesForDraw == 0 or countMovesForDraw == 1 or countMovesForDraw == 2 or countMovesForDraw == 3:
                countMovesForDraw += 1
            if countMovesForDraw == 4:
                positionHistory += gs.getBoardString()
                if previousPos == positionHistory:
                    COUNT_DRAW += 1
                    positionHistory = ""
                    countMovesForDraw = 0
                else:
                    previousPos = positionHistory
                    positionHistory = ""
                    countMovesForDraw = 0
                    COUNT_DRAW = 0
            # Call animateMove to animate the move
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            # genetare new set of valid move if valid move is made
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False

        drawGameState(screen, gs, validMoves, squareSelected, moveLogFont)

        if COUNT_DRAW == 1:
            gameOver = True
            text = 'Draw due to repetition'
            p.quit()
            # move_comparision_graph(bot_moves, player_moves)
            total_moves = 0
            bot_moves = 0
            player_moves = 0
            increment_game_index(i)  # Increment the game index
            # drawEndGameText(screen, text)
            print(text)


        if gs.stalemate:
            gameOver = True
            text = 'Stalemate'
            p.quit()
            # move_comparision_graph(bot_moves, player_moves)
            total_moves = 0
            bot_moves = 0
            player_moves = 0
            increment_game_index(i)  # Increment the game index
            # drawEndGameText(screen, text)
            print(text)
            # open("chess_moves.json", "w").close()

        elif gs.checkmate:
            gameOver = True
            text = 'Black wins by checkmate' if gs.whiteToMove else 'White wins by checkmate'
            if text == 'Black wins by checkmate': bot_win += 1
            else: player_win += 1
            p.quit()    
            # move_comparision_graph(bot_moves, player_moves)
            total_moves = 0
            bot_moves = 0
            player_moves = 0
            increment_game_index(i)  # Increment the game index
            print(text)
            # drawEndGameText(screen, text)
            # open("chess_moves.json", "w").close()

        clock.tick(MAX_FPS)
        p.display.flip()



def drawGameState(screen, gs, validMoves, squareSelected, moveLogFont):
    drawSquare(screen)  # draw square on board
    highlightSquares(screen, gs, validMoves, squareSelected)
    drawPieces(screen, gs.board)
    drawMoveLog(screen, gs, moveLogFont)


def drawSquare(screen):
    global colors
    colors = [p.Color(LIGHT_SQUARE_COLOR), p.Color(DARK_SQUARE_COLOR)]
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = colors[((row + col) % 2)]
            p.draw.rect(screen, color, p.Rect(
                col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def highlightSquares(screen, gs, validMoves, squareSelected):
    if squareSelected != ():  # make sure there is a square to select
        row, col = squareSelected
        # make sure they click there own piece
        if gs.board[row][col][0] == ('w' if gs.whiteToMove else 'b'):
            # highlight selected piece square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(p.Color(MOVE_HIGHLIGHT_COLOR))
            screen.blit(s, (col*SQ_SIZE, row*SQ_SIZE))
            # highlighting valid square
            s.fill(p.Color(POSSIBLE_MOVE_COLOR))
            for move in validMoves:
                if move.startRow == row and move.startCol == col:
                    screen.blit(s, (move.endCol*SQ_SIZE, move.endRow*SQ_SIZE))


def drawPieces(screen, board):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(
                    col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def drawMoveLog(screen, gs, font):
    # rectangle
    moveLogRect = p.Rect(
        BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color(LIGHT_SQUARE_COLOR), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []

    for i in range(0, len(moveLog), 2):
        moveString = " " + str(i//2 + 1) + ". " + str(moveLog[i]) + " "
        if i+1 < len(moveLog):
            moveString += str(moveLog[i+1])
        moveTexts.append(moveString)

    movesPerRow = 3
    padding = 10  # Increase padding for better readability
    lineSpacing = 5  # Increase line spacing for better separation
    textY = padding

    for i in range(0, len(moveTexts), movesPerRow):
        text = ""
        for j in range(movesPerRow):
            if i + j < len(moveTexts):
                text += moveTexts[i+j]

        textObject = font.render(text, True, p.Color('black'))

        # Adjust text location based on padding and line spacing
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)

        textY += textObject.get_height() + lineSpacing


def animateMove(move, screen, board, clock):
    global colors
    # change in row, col
    deltaRow = move.endRow - move.startRow
    deltaCol = move.endCol - move.startCol
    framesPerSquare = 5  # frames move one square
    frameCount = (abs(deltaRow) + abs(deltaCol)) * framesPerSquare
    # generate all the coordinates
    for frame in range(frameCount + 1):
        row, col = ((move.startRow + deltaRow*frame/frameCount, move.startCol +
                    deltaCol*frame/frameCount))  # how far through the animation
        # for each frame draw the moved piece
        drawSquare(screen)
        drawPieces(screen, board)

        # erase the piece moved from its ending squares
        color = colors[(move.endRow + move.endCol) % 2]  # get color of the square
        endSquare = p.Rect(move.endCol*SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)  # pygame rectangle
        p.draw.rect(screen, color, endSquare)

        # draw the captured piece back
        if move.pieceCaptured != '--':
            if move.isEnpassantMove:
                enPassantRow = move.endRow + \
                    1 if move.pieceCaptured[0] == 'b' else move.endRow - 1
                endSquare = p.Rect(move.endCol*SQ_SIZE, enPassantRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)  # pygame rectangle
            screen.blit(IMAGES[move.pieceCaptured], endSquare)

        # draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(
            col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))

        p.display.flip()
        clock.tick(240)


def drawEndGameText(screen, text):
    # create font object with type and size of font you want
    font = p.font.SysFont("Times New Roman", 30, False, False)
    # use the above font and render text (0 ? antialias)
    textObject = font.render(text, True, p.Color('black'))

    # Get the width and height of the textObject
    text_width = textObject.get_width()
    text_height = textObject.get_height()

    # Calculate the position to center the text on the screen
    textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(
        BOARD_WIDTH/2 - text_width/2, BOARD_HEIGHT/2 - text_height/2)

    # Blit the textObject onto the screen at the calculated position
    screen.blit(textObject, textLocation)

    textObject = font.render(text, 0, p.Color('Black'))
    screen.blit(textObject, textLocation.move(1, 1))


if __name__ == "__main__":
    main()

