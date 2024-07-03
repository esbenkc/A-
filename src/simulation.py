import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np


class Person:
    def __init__(self, name, role, join_date):
        self.name = name
        self.role = role  # 'F' for Founder, 'A' for A* holder
        self.startups = []
        self.performance = random.uniform(0.8, 1.2)
        self.join_date = join_date
        self.vesting_period = timedelta(days=730)  # 2 years
        self.fund_ownership = 0
        self.startup_ownerships = {}


class Startup:
    def __init__(self, name, start_date):
        self.name = name
        self.founders = []
        self.performance = random.uniform(0.8, 1.2)
        self.start_date = start_date
        self.status = "active"  # 'active', 'failed', or 'acquired'
        self.failure_date = None
        self.acquisition_date = None


class Fund:
    def __init__(self, name):
        self.name = name
        self.startups = []
        self.members = []
        self.total_value = 1000000  # Initial fund value


def calculate_vesting(person, current_date):
    time_in_fund = max(0, (current_date - person.join_date).days)
    vesting_factor = min(1, time_in_fund / person.vesting_period.days)
    return vesting_factor


def update_ownerships(fund, current_date):
    total_weight = sum(
        calculate_vesting(person, current_date) for person in fund.members
    )

    if total_weight > 0:
        for person in fund.members:
            vesting_factor = calculate_vesting(person, current_date)
            person.fund_ownership = vesting_factor / total_weight
    else:
        # If no one has started vesting yet, distribute ownership equally
        equal_share = 1 / len(fund.members)
        for person in fund.members:
            person.fund_ownership = equal_share

    for startup in fund.startups:
        if startup.status == "active":
            founder_weight = sum(
                calculate_vesting(f, current_date) for f in startup.founders
            )
            if founder_weight > 0:
                for founder in startup.founders:
                    vesting_factor = calculate_vesting(founder, current_date)
                    founder.startup_ownerships[startup.name] = (
                        vesting_factor / founder_weight
                    ) * 0.5  # Founders own 50% collectively
            else:
                # If no founder has started vesting yet, distribute ownership equally
                equal_share = 0.5 / len(startup.founders)
                for founder in startup.founders:
                    founder.startup_ownerships[startup.name] = equal_share
        elif startup.status == "failed":
            time_since_failure = (current_date - startup.failure_date).days
            decay_factor = max(
                0, 1 - (time_since_failure / 365)
            )  # Ownership decays over a year
            for founder in startup.founders:
                founder.startup_ownerships[startup.name] *= decay_factor


def simulate(days):
    start_date = datetime(2023, 1, 1)
    fund = Fund("A* Fund")

    # Create initial startups
    startup1 = Startup("Startup1", start_date)
    startup2 = Startup("Startup2", start_date + timedelta(days=60))
    startup3 = Startup("Startup3", start_date + timedelta(days=120))
    fund.startups = [startup1, startup2, startup3]

    # Create initial founders and A* holders
    founders = [
        Person(f"Founder_{i}", "F", startup.start_date)
        for i, startup in enumerate(fund.startups)
        for _ in range(2)  # 2 founders per startup
    ]
    a_holders = [Person(f"Advisor_{i}", "A", start_date) for i in range(3)]

    # Assign founders to startups
    for i, startup in enumerate(fund.startups):
        startup.founders = founders[i * 2 : (i + 1) * 2]
        for founder in startup.founders:
            founder.startups.append(startup)

    fund.members = founders + a_holders

    # Pre-allocate arrays for ownership history
    max_members = len(fund.members) + 2  # Added buffer for new startup founders
    fund_ownership_history = np.zeros((max_members, days))
    startup_ownership_history = np.zeros((max_members, days))
    fund_value_history = np.zeros(days)

    for day in range(days):
        current_date = start_date + timedelta(days=day)

        # Simulate events
        if day == 180:  # Startup1 fails after 6 months
            startup1.status = "failed"
            startup1.failure_date = current_date
        elif day == 300:  # Startup2 gets acquired after 10 months
            startup2.status = "acquired"
            startup2.acquisition_date = current_date
            acquisition_value = 5000000  # Hypothetical acquisition value
            fund.total_value += acquisition_value
        elif day == 365:  # New startup joins after 1 year
            new_startup = Startup("Startup4", current_date)
            new_founders = [
                Person(f"NewFounder_{i}", "F", current_date) for i in range(2)
            ]
            new_startup.founders = new_founders
            for founder in new_founders:
                founder.startups.append(new_startup)
            fund.startups.append(new_startup)
            fund.members.extend(new_founders)
            print(
                f"Day {day}: New startup 'Startup4' added with {len(new_founders)} founders."
            )

        update_ownerships(fund, current_date)

        # Record ownership history
        for i, person in enumerate(fund.members):
            fund_ownership_history[i, day] = person.fund_ownership
            if person.role == "F":
                startup_ownership = sum(
                    person.startup_ownerships.get(s.name, 0)
                    for s in person.startups
                    if s.status != "acquired"
                )
                startup_ownership_history[i, day] = startup_ownership

        fund_value_history[day] = fund.total_value

    return (
        fund_ownership_history,
        startup_ownership_history,
        fund_value_history,
        fund.members,
    )


# Run simulation
days_to_simulate = 730  # 2 years
fund_ownership_history, startup_ownership_history, fund_value_history, final_members = (
    simulate(days_to_simulate)
)

# Plotting
plt.figure(figsize=(15, 8))

# Plot fund ownership
for i, member in enumerate(final_members):
    plt.plot(
        range(days_to_simulate),
        fund_ownership_history[i],
        label=f"Fund ownership - {member.name}",
    )

# Plot startup ownership
for i, member in enumerate(final_members):
    if member.role == "F":
        plt.plot(
            range(days_to_simulate),
            startup_ownership_history[i],
            label=f"Startup ownership - {member.name}",
            linestyle="--",
        )

plt.title("Ownership Changes Over Time (Including New Startup)")
plt.xlabel("Days")
plt.ylabel("Ownership Percentage")
plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()
plt.grid(True)

# Save the plot as an SVG file
plt.savefig(
    "plot/ownership_changes_with_new_startup.svg", format="svg", bbox_inches="tight"
)
print(
    "Simulation completed and graph saved as 'ownership_changes_with_new_startup.svg'"
)
plt.figure(figsize=(20, 10))

time_points = range(0, days_to_simulate, 30)  # Every 30 days
num_startups = 4  # Including the new startup that joins after a year

vesting_period = 730  # 2 years in days

for i, t in enumerate(time_points):
    startup_bars = []
    for s in range(num_startups):
        if s < 3 or (
            s == 3 and t >= 365
        ):  # First 3 startups always show, 4th only after 1 year
            if s < 3:
                startup_start = 0
            else:
                startup_start = 365

            vesting_factor = min(1, max(0, (t - startup_start) / vesting_period))

            a_star = 0.5  # A* always owns 50%
            founder1 = 0.25 * vesting_factor
            founder2 = 0.25 * vesting_factor

            if t >= 180 and s == 0:  # Startup 1 fails after 6 months
                a_star, founder1, founder2 = 0, 0, 0
            elif t >= 300 and s == 1:  # Startup 2 gets acquired after 10 months
                a_star, founder1, founder2 = 1, 0, 0

            startup_bars.append([a_star, founder1, founder2])

    bottom = 0
    for bar in startup_bars:
        plt.bar(t, bar, bottom=bottom, width=20, color=["blue", "green", "orange"])
        bottom += 1

plt.title("Startup Ownership Structure Over Time")
plt.xlabel("Days")
plt.ylabel("Startups")
plt.yticks(range(num_startups), [f"Startup {i+1}" for i in range(num_startups)])
plt.axvline(x=180, color="r", linestyle="--", alpha=0.5, label="Startup 1 Failure")
plt.axvline(x=300, color="g", linestyle="--", alpha=0.5, label="Startup 2 Acquisition")
plt.axvline(x=365, color="b", linestyle="--", alpha=0.5, label="Startup 4 Joins")
plt.legend(
    ["A* Fund", "Founder 1", "Founder 2", "Failure", "Acquisition", "New Startup"]
)
plt.tight_layout()

plt.savefig(
    "plot/corrected_startup_ownership_structure.svg", format="svg", bbox_inches="tight"
)
print("Corrected plot saved as 'corrected_startup_ownership_structure.svg'")
# Print some debug information
print(f"Final number of members: {len(final_members)}")
print(f"Fund ownership history shape: {fund_ownership_history.shape}")
print(f"Startup ownership history shape: {startup_ownership_history.shape}")
print(f"Fund value history shape: {fund_value_history.shape}")
