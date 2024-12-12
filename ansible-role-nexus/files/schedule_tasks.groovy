import groovy.json.JsonSlurper
import org.sonatype.nexus.scheduling.TaskConfiguration
import org.sonatype.nexus.scheduling.TaskInfo
import org.sonatype.nexus.scheduling.TaskScheduler
import org.sonatype.nexus.scheduling.schedule.Monthly
import org.sonatype.nexus.scheduling.schedule.Schedule
import org.sonatype.nexus.scheduling.schedule.Weekly
import java.text.SimpleDateFormat

def parsedArgs = new JsonSlurper().parseText(args)
def taskScheduler = container.lookup(TaskScheduler.class.getName())

def existingTask = taskScheduler.listsTasks().find { TaskInfo taskInfo ->
    taskInfo.name == parsedArgs.name
}

if (existingTask && existingTask.getCurrentState().getRunState() != null) {
    log.info("Could not update currently running task: ${parsedArgs.name}")
    return
}

def taskConfiguration = taskScheduler.createTaskConfigurationInstance(parsedArgs.typeId)
if (existingTask) {
    taskConfiguration.setId(existingTask.getId())
}

configureTask(taskConfiguration, parsedArgs)

def schedule = createSchedule(taskScheduler, parsedArgs)
taskScheduler.scheduleTask(taskConfiguration, schedule)

void configureTask(TaskConfiguration config, def task) {
    config.with {
        setName(task.name)
        setAlertEmail(task.get('task_alert_email', '') as String)
        setEnabled(Boolean.valueOf(task.get('enabled', 'true') as String))

        task.taskProperties.each { key, value ->
            setString(key, value)
        }

        task.booleanTaskProperties.each { key, value ->
            setBoolean(key, Boolean.valueOf(value))
        }
    }
}

Schedule createSchedule(TaskScheduler taskScheduler, def task) {
    def dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss")
    def startDate = task.get('start_date_time') ? dateFormat.parse(task.start_date_time) : new Date()

    switch (task.get('schedule_type', 'cron')) {
        case 'manual':
            return taskScheduler.scheduleFactory.manual()
        case 'now':
            return taskScheduler.scheduleFactory.now()
        case 'once':
            return taskScheduler.scheduleFactory.once(startDate)
        case 'hourly':
            return taskScheduler.scheduleFactory.hourly(startDate)
        case 'daily':
            return taskScheduler.scheduleFactory.daily(startDate)
        case 'weekly':
            def weeklyDays = task.get('weekly_days', null)
            if (!weeklyDays) throw new IllegalArgumentException('Weekly schedule requires a weekly_days list parameter')
            def weekdays = weeklyDays.collect { Weekly.Weekday.valueOf(it) }
            return taskScheduler.scheduleFactory.weekly(startDate, weekdays)
        case 'monthly':
            def monthlyDays = task.get('monthly_days', null)
            if (!monthlyDays) throw new IllegalArgumentException('Monthly schedule requires a monthly_days list parameter')
            def calendarDays = monthlyDays.collect { Monthly.CalendarDay.day(it as Integer) }
            return taskScheduler.scheduleFactory.monthly(startDate, calendarDays)
        case 'cron':
            def cron = task.get('cron', null)
            if (!cron) throw new IllegalArgumentException('Cron schedule requires a cron expression')
            return taskScheduler.scheduleFactory.cron(startDate, cron)
        default:
            throw new IllegalArgumentException("Unknown schedule type: ${task.schedule_type}")
    }
}
