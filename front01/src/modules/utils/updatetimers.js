

class UpdateTickTimerCounter{
 constructor(){
  this.timers = {}
 }
 add = (key, timer) =>{
  this.timers[key] = timer
 }
 get = (key) =>{
  return this.timers[key] 
 }
 }


export let timerscounter = new UpdateTickTimerCounter()
