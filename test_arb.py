from arb_calculator import *

def test():
    print("Test 1: Normal vig (no arb): -110, -110")
    is_arb, prob, margin = detect_arbitrage([-110, -110])
    print(f"Arb? {is_arb}, Prob: {prob:.4f}, Margin: {margin:.4f}")
    print("-" * 30)
    
    print("Test 2: Small arb: +105, -102")
    is_arb, prob, margin = detect_arbitrage([105, -102])
    print(f"Arb? {is_arb}, Prob: {prob:.4f}, Margin: {margin:.4f}")
    if is_arb:
        s_a, s_b, gp, gp_pct = calculate_arb_stakes_from_max_stake(105, -102, 100)
        print(f"Max Stake: $100 -> Stake A: ${s_a}, Stake B: ${s_b}")
        print(f"Guaranteed Profit: ${gp} ({gp_pct*100:.2f}%)")
    print("-" * 30)
    
    print("Test 3: Huge arb: +150, -130")
    is_arb, prob, margin = detect_arbitrage([150, -130])
    print(f"Arb? {is_arb}, Prob: {prob:.4f}, Margin: {margin:.4f}")
    if is_arb:
        s_a, s_b, gp, gp_pct = calculate_arb_stakes_from_max_stake(150, -130, 200)
        print(f"Max Stake: $200 -> Stake A: ${s_a}, Stake B: ${s_b}")
        print(f"Guaranteed Profit: ${gp} ({gp_pct*100:.2f}%)")
    print("-" * 30)

if __name__ == "__main__":
    test()
