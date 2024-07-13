import time
class risk_probability:

    def __init__(self):
        twodice = [[0]*6 for i in range(6)]
        threedice = [[0]*6 for i in range(6)]

        # get number of ways to have two dice with particular values,
        # as well as three dice where the highest 2 have particular values
        for i in range(6):
            for j in range(6):
                twodice[min(i,j)][max(i,j)] += 1
                for k in range(6):
                    ordered = sorted([i,j,k])
                    threedice[ordered[1]][ordered[2]] += 1

        total2dice = sum(sum(arr) for arr in twodice)
        total3dice = sum(sum(arr) for arr in threedice)

        flawless3v2 = 0 # probability of attacker rolling 3 dice against 2 and losing no pieces
        flawless2v2 = 0 # probability of attacker rolling 2 dice against 2 and losing no pieces
        for h in range(5):
            for i in range(h,5):
                # prob of defender rolling rolling h and i
                # we divide by attacker sample space now to avoid doing it repeatedly later
                temp3v2 = float(twodice[h][i])/(total2dice*total3dice)
                temp2v2 = float(twodice[h][i])/(total2dice*total2dice)
                for j in range(h+1,6):
                    for k in range(i+1,6):
                        # going through all ways attacker can defeat two armies
                        # without losing anybody in the process.
                        flawless3v2 += temp3v2*threedice[j][k]
                        flawless2v2 += temp2v2*twodice[j][k]

        flawed3v2 = 0 # probability of attacker rolling 3v2 and each losing 1 piece
        flawed2v2 = 0 # probability of attacker rolling 2v2 and each losing 1 piece
        for h in range(5):
            for i in range(h,6):
                # prob of defender rolling h and i
                # once again we factor out division of attacker sample space
                temp3v2 = float(twodice[h][i])/(total2dice*total3dice)
                temp2v2 = float(twodice[h][i])/(total2dice*total2dice)
                for j in range(h+1,6):
                    for k in range(j,i+1):
                        # attacker defeats low die but loses to high die
                        flawed3v2 += temp3v2*threedice[j][k]
                        flawed2v2 += temp2v2*twodice[j][k]
                if i==5: continue # attacker cannot beat high die
                for j in range(h+1):
                    for k in range(i+1,6):
                        # attacker defeats high die but loses to low die
                        flawed3v2 += temp3v2*threedice[j][k]
                        flawed2v2 += temp2v2*twodice[j][k]

        fatal3v2 = 1-flawless3v2-flawed3v2 # attacker loses two when rolling 3
        fatal2v2 = 1-flawless2v2-flawed2v2 # attacker loses two when rolling 2

        flawless1v2 = 0 # probability of attacker rolling 1 die and winning against 2 dice
        for i in range(5):
            for j in range(i,5):
                # prob of defender rolling i and j
                # factor out division by six (attacker sample space)
                temp1v2 = float(twodice[i][j])/(total2dice*6)
                for k in range(j+1,6):
                    flawless1v2 += temp1v2

        fatal1v2 = 1-flawless1v2 # probability of attacker rolling 1v2 and losing

        flawless3v1 = 0 # probability of attacker rolling 3v1 and winning
        flawless2v1 = 0 # probability of attacker rolling 2v1 and winning
        for i in range(5):
            temp3v1 = 1.0/(6*total3dice)
            temp2v1 = 1.0/(6*total2dice)
            for j in range(6):
                for k in range(max(j,i+1),6):
                    flawless3v1 += temp3v1*threedice[j][k]
                    flawless2v1 += temp2v1*twodice[j][k]

        fatal3v1 = 1-flawless3v1 # probability of attacker rolling 3v1 and losing
        fatal2v1 = 1-flawless2v1 # probabiliyy of attacker rolling 2v1 and losing


        flawless1v1 = 0 # prob of attacker rolling 1v1 and winning
        for i in range(5):
            for j in range(i+1,6):
                flawless1v1 += 1.0/36

        fatal1v1 = 1-flawless1v1

        # self.probs[x][y][z] means probability of attacker using x dice vs y dice with outcome z
        # (z=0 is a win, z=1 is a tie, z=2 is a loss)
        self.probs = [0, [0, [flawless1v1,0.0,fatal1v1], [flawless1v2,0.0,fatal1v2]],
                    [0, [flawless2v1,0.0,fatal2v1], [flawless2v2,flawed2v2,fatal2v2]],
                    [0, [flawless3v1,0.0,fatal3v1], [flawless3v2,flawed3v2,fatal3v2]]]
        self.bmem = {}
        self.omem = {}
        self.tmem = {}

    # Finds probability that army of size attackers will
    # defeat army of size defenders with at least minleft troops left.
    # Less general than outcomeprob.
    def battleprob(self,attackers, defenders, minleft=1):
        if attackers < minleft: return 0.0
        if defenders == 0: return 1.0

        h = (attackers, defenders, minleft)
        if h in self.bmem: return self.bmem[h]

        val = 0.0
        if attackers >= 3 and defenders >= 2:
            val = self.probs[3][2][0]*self.battleprob(attackers, defenders-2, minleft) + \
                self.probs[3][2][1]*self.battleprob(attackers-1, defenders-1, minleft) + \
                self.probs[3][2][2]*self.battleprob(attackers-2, defenders, minleft)
        elif attackers >= 3 and defenders == 1:
            val = self.probs[3][1][0] + \
                self.probs[3][1][2]*self.battleprob(attackers-1, defenders, minleft)
        elif attackers == 2 and defenders >= 2:
            val = self.probs[2][2][0]*self.battleprob(attackers, defenders-2, minleft) + \
                self.probs[2][2][1]*self.battleprob(attackers-1, defenders-1, minleft) + \
                self.probs[2][2][2]*self.battleprob(attackers-2, defenders, minleft)
        elif attackers == 2 and defenders == 1:
            val = self.probs[2][1][0] + \
                self.probs[2][1][2]*self.battleprob(attackers-1, defenders, minleft)
        elif attackers == 1 and defenders >= 2:
            val = self.probs[1][2][0]*self.battleprob(attackers, defenders-1, minleft)
        elif attackers == 1 and defenders == 1:
            val = self.probs[1][1][0]

        self.bmem[h] = val
        return val

    # Finds probability that an army of size attackers
    # battling an army of size defenders will result in
    # arem attackers and drem attackers remaining on either side.
    def outcomeprob(self,attackers, defenders, arem=1, drem=0):
        if attackers < arem or defenders < drem: return 0.0
        if defenders == drem:
            if drem == 0 and attackers != arem: return 0.0
            if attackers == arem: return 1.0

        h = (attackers, defenders, arem, drem)
        if h in self.omem: return self.omem[h]

        val = 0.0
        if attackers >= 3 and defenders >= 2:
            val = self.probs[3][2][0]*self.outcomeprob(attackers, defenders-2, arem, drem) + \
                self.probs[3][2][1]*self.outcomeprob(attackers-1, defenders-1, arem, drem) + \
                self.probs[3][2][2]*self.outcomeprob(attackers-2, defenders, arem, drem)
        elif attackers >= 3 and defenders == 1:
            val = self.probs[3][1][0]*self.outcomeprob(attackers, defenders-1, arem, drem) + \
                self.probs[3][1][2]*self.outcomeprob(attackers-1, defenders, arem, drem)
        elif attackers == 2 and defenders >= 2:
            val = self.probs[2][2][0]*self.outcomeprob(attackers, defenders-2, arem, drem) + \
                self.probs[2][2][1]*self.outcomeprob(attackers-1, defenders-1, arem, drem) + \
                self.probs[2][2][2]*self.outcomeprob(attackers-2, defenders, arem, drem)
        elif attackers == 2 and defenders == 1:
            val = self.probs[2][1][0]*self.outcomeprob(attackers, defenders-1, arem, drem) + \
                self.probs[2][1][2]*self.outcomeprob(attackers-1, defenders, arem, drem)
        elif attackers == 1 and defenders >= 2:
            val = self.probs[1][2][0]*self.outcomeprob(attackers, defenders-1, arem, drem)
        elif attackers == 1 and defenders == 1:
            val = self.probs[1][1][0]*self.outcomeprob(attackers, defenders-1, arem, drem)

        self.omem[h] = val
        return val

    # Finds probability of successful tour given:
    # a starting army of size attackers,
    # an array of armies darmies representing the defending armies in the order they will be attacked,
    # which defending army is being attacked (default 0 for the start),
    # the number of troops we want to leave behind at each country (default 1 for each country),
    # number of guys we want to leave behind in each country
    def tourprob(self,attackers, darmies, tindex=0, fortify=([1]*100)):
        if tindex == len(darmies): return 1.0
        if tindex == 0: # reset memoize table
            global tmem
            tmem = {}

        h = (attackers, tindex)
        if h in tmem: return tmem[h]

        army = attackers-fortify[tindex]
        minremaining = sum(fortify[i] for i in range(tindex+1,len(darmies)+1))

        val = 0.0
        for i in range(minremaining, army+1):
            val += self.outcomeprob(army, darmies[tindex], i)*self.tourprob(i, darmies, tindex+1, fortify)

        tmem[h] = val
        return val
    
test = risk_probability()
#attacker,defender
start = time.perf_counter()

# print(f"Before: {(time.perf_counter() - start)*1000}")
# print(test.battleprob(669,1609))
# print(f"Before: {(time.perf_counter() - start)*1000}")


print(f"Before: {(time.perf_counter() - start)*1000}")
print(test.battleprob(2,2))
print(f"Before: {(time.perf_counter() - start)*1000}")

