```java
@Override
public double calculatePhaseTimeGradient(AbstractPhaseScope<Solution_> phaseScope) {
    var timeGradient = 1.0;
    for (var termination : phaseTerminationList) {
        var nextTimeGradient = termination.calculatePhaseTimeGradient(phaseScope);
        timeGradient = Math.min(timeGradient, nextTimeGradient);
    }
    return timeGradient;
}
```