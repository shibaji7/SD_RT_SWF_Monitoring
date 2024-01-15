let calendar = document.querySelector('.calendar')

fetchEvent = (date) => {
    let color = 'white'
    for(i = 0; i<EVENTS.length; i++){
        e = EVENTS[i]
        if(e['date'].getTime()===date.getTime()){
            color = e['color']
            break
        }
    }
    return color
}

const month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

isLeapYear = (year) => {
    return (year % 4 === 0 && year % 100 !== 0 && year % 400 !== 0) || (year % 100 === 0 && year % 400 ===0)
}

getFebDays = (year) => {
    return isLeapYear(year) ? 29 : 28
}

generateCalendar = (month, year) => {
    console.log(year, month)
    let calendar_days = calendar.querySelector('.calendar-days')
    let calendar_header_year = calendar.querySelector('#year')

    let days_of_month = [31, getFebDays(year), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    calendar_days.innerHTML = ''

    let currDate = new Date()
    if (month > 11 || month < 0) month = currDate.getMonth()
    if (!year) year = currDate.getFullYear()

    let curr_month = `${month_names[month]}`
    month_picker.innerHTML = curr_month
    calendar_header_year.innerHTML = year
    console.log(year, month)
    // get first day of month
    
    let first_day = new Date(year, month, 1)
    let tag = `<span></span>
    <span></span>
    <span></span>
    <span></span>`
    for (let i = 0; i <= days_of_month[month] + first_day.getDay() - 1; i++) {
        let day = document.createElement('div')
        if (i >= first_day.getDay()) {
            day.classList.add('calendar-day-hover')
            day.innerHTML = i - first_day.getDay() + 1
            day.innerHTML += tag
            let date = new Date(first_day.getFullYear(), first_day.getMonth(), i - first_day.getDay()+1)
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
        day.addEventListener('click', function(e){
            let href = window.location.href.replace('calender.html', '')
            let date = e.target.innerHTML.replace(tag, '')
            let month = first_day.getMonth() + 1
            let year = first_day.getFullYear()
            if (month<=9){
                month = '0' + month.toString()
            }
            if (date<=9){
                date = '0' + date.toString()
            }
            file = year.toString()+month.toString()+date+".png";
            goes_img = "../assets/data/figures/goes/" + file;
            sd_img = "../assets/data/figures/rads/" + file;
            // folder = 'events/' + year + '-' + month + '-' + date + '/'
            // let summary_page = href + folder + 'summary.html'
            console.log(goes_img, sd_img);
            // location.assign(summary_page)
            document.getElementById('calendar_pane').style.display = "none";
            document.getElementById('button_image').style.display = "block";
            document.querySelector('#goes_image').innerHTML = `<img src="${goes_img}" alt="GOES Flare Info">`;
            document.querySelector('#sd_image').innerHTML = `<img src="${sd_img}" alt="SD SWF Info">`;
        })
        calendar_days.appendChild(day)
    }
}

click_back = () =>{
    document.getElementById('calendar_pane').style.display = "block";
    document.getElementById('button_image').style.display = "none";
    history.back();
}
let month_list = calendar.querySelector('.month-list')

month_names.forEach((e, index) => {
    let month = document.createElement('div')
    month.innerHTML = `<div data-month="${index}">${e}</div>`
    month.querySelector('div').onclick = () => {
        month_list.classList.remove('show')
        curr_month.value = index
        generateCalendar(index, curr_year.value)
    }
    month_list.appendChild(month)
})

let month_picker = calendar.querySelector('#month-picker')

month_picker.onclick = () => {
    month_list.classList.add('show')
}

let currDate = new Date()

let curr_month = {value: currDate.getMonth()}
let curr_year = {value: currDate.getFullYear()}

generateCalendar(curr_month.value, curr_year.value)

document.querySelector('#prev-year').onclick = () => {
    --curr_year.value
    generateCalendar(curr_month.value, curr_year.value)
}

document.querySelector('#next-year').onclick = () => {
    ++curr_year.value
    generateCalendar(curr_month.value, curr_year.value)
}

document.querySelector('#prev-month').onclick = () => {
    --curr_month.value
    if (curr_month.value==-1){
        curr_month.value = 11
        --curr_year.value
    }
    generateCalendar(curr_month.value, curr_year.value)
}

document.querySelector('#next-month').onclick = () => {
    ++curr_month.value
    if (curr_month.value==12){
        curr_month.value = 0
        ++curr_year.value
    }
    generateCalendar(curr_month.value, curr_year.value)
}

