import random

pieceScore = {"K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "p": 1}

knightScores = [[1, 1, 1, 1, 1, 1, 1, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 1, 1, 1, 1, 1, 1, 1]]

bishopScores =  [[4, 3, 2, 1, 1, 2, 3, 4],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [4, 3, 2, 1, 1, 2, 3, 4]]

queenScores =  [[1, 1, 1, 3, 1, 1, 1, 1],
                [1, 2, 3, 3, 3, 1, 1, 1],
                [1, 4, 3, 3, 3, 4, 2, 1],
                [1, 2, 3, 3, 3, 2, 2, 1],
                [1, 2, 3, 3, 3, 2, 2, 1],
                [1, 4, 3, 3, 3, 4, 2, 1],
                [1, 1, 2, 3, 3, 1, 1, 1],
                [1, 1, 1, 3, 1, 1, 1, 1]]

rookScores =   [[4, 3, 4, 4, 4, 4, 3, 4],
                [4, 4, 4, 4, 4, 4, 4, 4],
                [1, 1, 2, 3, 3, 2, 1, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 1, 2, 2, 2, 2, 1, 1],
                [4, 4, 4, 4, 4, 4, 4, 4],
                [4, 3, 2, 1, 1, 2, 3, 4]]

whitePawnScores =  [[8, 8, 8, 8, 8, 8, 8, 8],
                    [8, 8, 8, 8, 8, 8, 8, 8],
                    [5, 6, 6, 7, 7, 6, 6, 5],
                    [2, 3, 3, 5, 5, 3, 3, 2],
                    [1, 2, 3, 4, 4, 3, 2, 1],
                    [1, 1, 2, 3, 3, 2, 1, 1],
                    [1, 1, 1, 0, 0, 1, 1, 1],
                    [0, 0, 0, 0, 0, 0, 0, 0]]

blackPawnScores =  [[0, 0, 0, 0, 0, 0, 0, 0],
                    [1, 1, 1, 0, 0, 1, 1, 1],
                    [1, 1, 2, 3, 3, 2, 1, 1],
                    [1, 2, 3, 4, 4, 3, 2, 1],
                    [2, 3, 3, 5, 5, 3, 3, 2],
                    [5, 6, 6, 7, 7, 6, 6, 5],
                    [8, 8, 8, 8, 8, 8, 8, 8],
                    [8, 8, 8, 8, 8, 8, 8, 8]]


piecePositionScores = {"N": knightScores, "B": bishopScores, "Q": queenScores, "R": rookScores, "wp": whitePawnScores, "bp": blackPawnScores}


CHECKMATE = 1000
STALEMATE = 0
DEPTH = 3
SET_WHITE_AS_BOT = -1 



def findRandomMoves(validMoves):
    return validMoves[random.randint(0, len(validMoves) - 1)]



def findBestMove(gs, validMoves, returnQueue):
    global nextMove, whitePawnScores, blackPawnScores
    nextMove = None
    random.shuffle(validMoves)

    if gs.playerWantsToPlayAsBlack:
        # Swap the variables
        whitePawnScores, blackPawnScores = blackPawnScores, whitePawnScores

    SET_WHITE_AS_BOT = 1 if gs.whiteToMove else -1

    findMoveNegaMaxAlphaBeta(gs, validMoves, DEPTH, -CHECKMATE, CHECKMATE,  SET_WHITE_AS_BOT)

    returnQueue.put(nextMove)



def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    global nextMove
    if depth == 0:
        return turnMultiplier * scoreBoard(gs)


    maxScore = -CHECKMATE
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()  # opponent validmoves
        score = - \
            findMoveNegaMaxAlphaBeta(
                gs, nextMoves, depth-1, -beta, -alpha, -turnMultiplier)
        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
                print(move, score)
        gs.undoMove()
        if maxScore > alpha:
            alpha = maxScore  # alpha is the new max
        if alpha >= beta:  # if we find new max is greater than minimum so far in a branch then we stop iterating in that branch as we found a worse move in that branch
            break
    return maxScore



def scoreBoard(gs):
    if gs.checkmate:
        if gs.whiteToMove:
            gs.checkmate = False
            return -CHECKMATE  # black wins
        else:
            gs.checkmate = False
            return CHECKMATE  # white wins
    elif gs.stalemate:
        return STALEMATE

    score = 0
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            square = gs.board[row][col]
            if square != "--":
                piecePositionScore = 0
                # score positionally based on piece type
                if square[1] != "K":
                    # return score of the piece at that position
                    if square[1] == "p":
                        piecePositionScore = piecePositionScores[square][row][col]
                    else:
                        piecePositionScore = piecePositionScores[square[1]][row][col]
                if SET_WHITE_AS_BOT:
                    if square[0] == 'w':
                        score += pieceScore[square[1]] + \
                            piecePositionScore * .1
                    elif square[0] == 'b':
                        score -= pieceScore[square[1]] + \
                            piecePositionScore * .1
                else:
                    if square[0] == 'w':
                        score -= pieceScore[square[1]] + \
                            piecePositionScore * .1
                    elif square[0] == 'b':
                        score += pieceScore[square[1]] + \
                            piecePositionScore * .1

    return score



