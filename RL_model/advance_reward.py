import numpy as np

def advanced_reward_function(history, enable_risk_management=True, 
                             enable_transaction_costs=True, 
                             enable_benchmark_comparison=True, 
                             enable_long_term_growth=True, 
                             enable_sharpe_ratio=True, 
                             enable_drawdown_penalty=True):
    """
    Advanced reward function for trading environment.
    
    Args:
        history (dict): Dictionary containing historical data for the portfolio, actions, and benchmark.
        enable_risk_management (bool): Penalize high drawdowns or volatility.
        enable_transaction_costs (bool): Penalize based on trading costs.
        enable_benchmark_comparison (bool): Reward based on outperformance against a benchmark.
        enable_long_term_growth (bool): Reward long-term portfolio growth.
        enable_sharpe_ratio (bool): Include a Sharpe ratio component in the reward.
        enable_drawdown_penalty (bool): Penalize for significant drawdowns.
    
    Returns:
        float: Calculated reward value for the current step.
    """
    # Extract portfolio valuation and benchmark (if available)
    portfolio_valuation = history["portfolio_valuation"]
    # actions = history["actions"]
    # benchmark_valuation = history.get("benchmark_valuation", None)

    # Ensure we have at least two data points to calculate returns
    if len(portfolio_valuation) < 2:
        return 0.0

    # Logarithmic return
    log_return = np.log(portfolio_valuation[-1] / portfolio_valuation[-2])

    # Initialize reward
    reward = log_return

    # Risk management (drawdown penalty)
    if enable_risk_management:
        drawdown_penalty = max(0, (max(portfolio_valuation) - portfolio_valuation[-1]) / max(portfolio_valuation))
        reward -= 0.1 * drawdown_penalty

    # # Transaction costs
    # if enable_transaction_costs:
    #     # Assuming a fixed cost per trade (adjust as needed)
    #     cost_per_trade = 0.001
    #     reward -= cost_per_trade * abs(actions[-1])  # Penalize for actions

    # Benchmark comparison
    # if enable_benchmark_comparison and benchmark_valuation is not None:
    #     benchmark_return = np.log(benchmark_valuation[-1] / benchmark_valuation[-2])
    #     reward -= benchmark_return  # Reward relative outperformance

    # Long-term growth
    if enable_long_term_growth:
        cumulative_growth = np.log(portfolio_valuation[-1] / portfolio_valuation[0])
        reward += 0.01 * cumulative_growth

    # Sharpe ratio (risk-adjusted return)
    if enable_sharpe_ratio:
        if len(portfolio_valuation) >= 10:  # Ensure at least 10 steps for volatility calculation
            rolling_volatility = np.std(portfolio_valuation[-10:])
            mean_return = np.mean(np.diff(np.log(portfolio_valuation[-10:])))
            sharpe_ratio = mean_return / (rolling_volatility + 1e-8)
            reward += 0.1 * sharpe_ratio

    # Drawdown penalty (specific penalty component for excessive losses)
    if enable_drawdown_penalty:
        drawdown = (max(portfolio_valuation) - portfolio_valuation[-1]) / max(portfolio_valuation)
        reward -= 0.1 * drawdown if drawdown > 0.2 else 0  # Penalize only if drawdown > 20%

    return reward
