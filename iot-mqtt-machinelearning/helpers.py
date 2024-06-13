


weekday_map = {'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4, 'friday': 5, 'saturday': 6}
open_close_map = {'closed': 0, 'open': 1}
truth_map = {'FALSE': 0, 'TRUE': 1}

# Function to convert time stamp string to seconds
def time_to_seconds(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60 + seconds

def convert_features(feature):
    time = time_to_seconds(feature.time)
    day = weekday_map[str(feature.day.value)]
    motion = 1 if feature.motion else 0
    temp_df = feature.temp_df

    return [time, day, motion, temp_df]

def predict_map(predictions):
    results = []
    for predict in predictions:
        if predict == 0:
            results.append('off')
        else:
            results.append('on')

    return results

def fahrenheit_to_celsius(fahrenheit):
    celsius = (fahrenheit - 32) * 5/9
    return round(celsius, 1)


