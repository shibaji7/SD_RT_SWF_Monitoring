var calendar = document.querySelector('#calendar_pane_swf')

fetchEvent = (date) => {
    var color = 'white'
    for(i = 0; i<EVENTS.length; i++){
        e = EVENTS[i]
        if(e['date'].getTime()===date.getTime()){
            color = e['color']
            break
        }
    }
    return color
}

var month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

isLeapYear = (year) => {
    return (year % 4 === 0 && year % 100 !== 0 && year % 400 !== 0) || (year % 100 === 0 && year % 400 ===0)
}

getFebDays = (year) => {
    return isLeapYear(year) ? 29 : 28
}

set_inner_html = (id_str, file, alter) => {
    var div = document.querySelector(id_str);
    if (div){
        div.innerHTML = `<img src="${file}" alt="${alter}">`;
    }
}

generateCalendar = (month, year) => {
    console.log(year, month)
    var calendar_days = calendar.querySelector('#calendar-days-swf')
    var calendar_header_year = calendar.querySelector('#year-swf')

    var days_of_month = [31, getFebDays(year), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    calendar_days.innerHTML = ''

    var currDate = new Date()
    if (month > 11 || month < 0) month = currDate.getMonth()
    if (!year) year = currDate.getFullYear()

    var curr_month = `${month_names[month]}`
    month_picker.innerHTML = curr_month
    calendar_header_year.innerHTML = year
    console.log(year, month)
    // get first day of month
    
    var first_day = new Date(year, month, 1)
    var tag = `<span></span>
    <span></span>
    <span></span>
    <span></span>`
    for (var i = 0; i <= days_of_month[month] + first_day.getDay() - 1; i++) {
        var day = document.createElement('div')
        if (i >= first_day.getDay()) {
            day.classList.add('calendar-day-hover')
            day.innerHTML = i - first_day.getDay() + 1
            day.innerHTML += tag
            var date = new Date(first_day.getFullYear(), first_day.getMonth(), i - first_day.getDay()+1)
            color = fetchEvent(date)
            // if (i - first_day.getDay() === currDate.getDate() && year === currDate.getFullYear() && month === currDate.getMonth()) {
            //     day.classList.add('curr-date')
            // }
            if(color=='red'){
                day.classList.add('x-class-date')
            }
            if(color=='yellow'){
                day.classList.add('m-class-date')
            }
            if(color=='green'){
                day.classList.add('c-class-date')
            }
        }
        calendar_days.appendChild(day)
    }
}

click_back = () =>{
    location.reload();
}
var month_list = calendar.querySelector('#month-list-swf')

month_names.forEach((e, index) => {
    var month = document.createElement('div')
    month.innerHTML = `<div data-month="${index}">${e}</div>`
    month.querySelector('div').onclick = () => {
        month_list.classList.remove('show')
        curr_month.value = index
        generateCalendar(index, curr_year.value)
    }
    month_list.appendChild(month)
})

var month_picker = calendar.querySelector('#month-picker-swf')

month_picker.onclick = () => {
    month_list.classList.add('show')
}

var currDate = new Date()
currDate.setDate(currDate.getDate() - 1)

var curr_month = {value: currDate.getMonth()}
var curr_year = {value: currDate.getFullYear()}

generateCalendar(curr_month.value, curr_year.value)

document.querySelector('#prev-year-swf').onclick = () => {
    --curr_year.value
    generateCalendar(curr_month.value, curr_year.value)
}

document.querySelector('#next-year-swf').onclick = () => {
    ++curr_year.value
    generateCalendar(curr_month.value, curr_year.value)
}

document.querySelector('#prev-month-swf').onclick = () => {
    --curr_month.value
    if (curr_month.value==-1){
        curr_month.value = 11
        --curr_year.value
    }
    generateCalendar(curr_month.value, curr_year.value)
}

document.querySelector('#next-month-swf').onclick = () => {
    ++curr_month.value
    if (curr_month.value==12){
        curr_month.value = 0
        ++curr_year.value
    }
    generateCalendar(curr_month.value, curr_year.value)
}

