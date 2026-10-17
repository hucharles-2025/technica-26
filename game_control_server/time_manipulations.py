
# Returns the minuted timestamp which corresponds to the 
# hour and minute provided.
#  h = hours in 24 hour time
#  m = minutes
def get_minutes(h, m):
    return (60 * h) + m

# Prints out a string like "14:45"
# in response to a minuted timestmap
def get_time_string(mst):
    hour = mst // 60
    mst = mst % 60
    return f"{hour}:{mst}" 

# Prints out a time diff in "1h 2m" format
# based on a diff reported in # minutes
def get_time_diff(md):
    hour = md // 60
    md = md % 60
    return f"{hour}hr {mst}min"