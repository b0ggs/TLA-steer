----------------------------- MODULE TwoLights -----------------------------
(***************************************************************************)
(* Two traffic lights, A then B, on the same road, coupled by a shared     *)
(* clock and staged by a fixed phase offset.                               *)
(*                                                                          *)
(* Written to be compiled into Python and checked for exact refinement.     *)
(* Three properties matter for that purpose:                                *)
(*                                                                          *)
(*   1. `clock` is shared. Every one of the six light actions must leave it *)
(*      alone. That is six chances to drop an UNCHANGED obligation.         *)
(*                                                                          *)
(*   2. The A actions and the B actions are structurally identical and      *)
(*      differ only in which variables they touch and which they must       *)
(*      preserve. That is the copy-paste trap: an implementation that       *)
(*      duplicates AGreenToYellow and forgets to swap a name in UNCHANGED   *)
(*      reads as correct code and is not.                                   *)
(*                                                                          *)
(*   3. The state space is finite and small, so TLC enumerates it fully and *)
(*      refinement can be decided exactly rather than sampled.              *)
(***************************************************************************)
EXTENDS Naturals

CONSTANTS CycleLength,   \* clock wraps here; keeps the state space finite
          MinGreen,      \* a light may not leave green before this many ticks
          MinYellow,
          MinRed,
          MaxPhase,      \* hard cap: at this many ticks a light must change
          Offset         \* how far into red light B starts, staging the pair

VARIABLES clock,         \* shared. advanced only by Tick.
          lightA, timerA,
          lightB, timerB

vars == <<clock, lightA, timerA, lightB, timerB>>

Colors == {"red", "green", "yellow"}

(* A light MAY change once it has served its minimum phase. It MUST change  *)
(* at MaxPhase, which is what bounds the timers and the state space.        *)
(* The gap between the two is where the nondeterminism lives: for several   *)
(* ticks the spec permits both waiting and changing, and an implementation  *)
(* has to admit exactly that set of behaviours. Not fewer, not more.        *)
TypeOK ==
    /\ clock  \in 0..(CycleLength - 1)
    /\ lightA \in Colors
    /\ lightB \in Colors
    /\ timerA \in 0..MaxPhase
    /\ timerB \in 0..MaxPhase

Init ==
    /\ clock  = 0
    /\ lightA = "green"
    /\ timerA = 0
    /\ lightB = "red"
    /\ timerB = Offset

(*-------------------------------------------------------------------------*)
(* Time. The only action that touches the shared clock, and the only one   *)
(* that touches both lights. Disabled once either timer reaches MaxPhase,  *)
(* which forces that light to change and bounds the state space.           *)
(*-------------------------------------------------------------------------*)
Tick ==
    /\ timerA < MaxPhase
    /\ timerB < MaxPhase
    /\ clock'  = (clock + 1) % CycleLength
    /\ timerA' = timerA + 1
    /\ timerB' = timerB + 1
    /\ UNCHANGED <<lightA, lightB>>

(*-------------------------------------------------------------------------*)
(* Light A. Must preserve clock and all of light B.                        *)
(*-------------------------------------------------------------------------*)
AGreenToYellow ==
    /\ lightA = "green"
    /\ timerA >= MinGreen
    /\ lightA' = "yellow"
    /\ timerA' = 0
    /\ UNCHANGED <<clock, lightB, timerB>>

AYellowToRed ==
    /\ lightA = "yellow"
    /\ timerA >= MinYellow
    /\ lightA' = "red"
    /\ timerA' = 0
    /\ UNCHANGED <<clock, lightB, timerB>>

ARedToGreen ==
    /\ lightA = "red"
    /\ timerA >= MinRed
    /\ lightA' = "green"
    /\ timerA' = 0
    /\ UNCHANGED <<clock, lightB, timerB>>

(*-------------------------------------------------------------------------*)
(* Light B. Identical in shape. Must preserve clock and all of light A.    *)
(*-------------------------------------------------------------------------*)
BGreenToYellow ==
    /\ lightB = "green"
    /\ timerB >= MinGreen
    /\ lightB' = "yellow"
    /\ timerB' = 0
    /\ UNCHANGED <<clock, lightA, timerA>>

BYellowToRed ==
    /\ lightB = "yellow"
    /\ timerB >= MinYellow
    /\ lightB' = "red"
    /\ timerB' = 0
    /\ UNCHANGED <<clock, lightA, timerA>>

BRedToGreen ==
    /\ lightB = "red"
    /\ timerB >= MinRed
    /\ lightB' = "green"
    /\ timerB' = 0
    /\ UNCHANGED <<clock, lightA, timerA>>

Next ==
    \/ Tick
    \/ AGreenToYellow
    \/ AYellowToRed
    \/ ARedToGreen
    \/ BGreenToYellow
    \/ BYellowToRed
    \/ BRedToGreen

Spec == Init /\ [][Next]_vars

(*-------------------------------------------------------------------------*)
(* Invariants. Checked by TLC, and a second signal on refinement: an        *)
(* implementation that violates one of these is wrong in a way you can      *)
(* point at, not just in the transition graph.                              *)
(*-------------------------------------------------------------------------*)
TimersBounded ==
    /\ timerA <= MaxPhase
    /\ timerB <= MaxPhase

(* Not an invariant. A predicate over states, so the fraction of the        *)
(* reachable graph satisfying it can be counted directly. This is the hook  *)
(* for the green-wave question, answered by counting rather than simulating.*)
GreenWave == (lightA = "green") /\ (lightB = "green")
=============================================================================
