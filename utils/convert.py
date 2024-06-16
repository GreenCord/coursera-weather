def convertTemperature(degrees, toUnit):
    if toUnit == "C":
        return (degrees - 32) * 5 / 9
    elif toUnit == "F":
        return (degrees * 9 / 5) + 32
    else: return "Error"