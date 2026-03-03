class Hand{ //metoda reprezentujaca wskazowke
    constructor(length, width, color){
        this.lenght=length;
        this.width=width;
        this.color=color;
    }
    draw(ctx, angle) {
        ctx.save();
        ctx.rotate(angle); //obraca uklad wspolrzednych o podany kat
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, -this.lenght);

        ctx.lineWidth = this.width;
        ctx.strokeStyle = this.color;
        ctx.lineCap = "round";

        ctx.stroke();
        ctx.restore(); //cofa obrot
    }
} 
class Clock{
    constructor(canvas){
        this.canvas=canvas;
        this.ctx=canvas.getContext("2d");
        this.width = canvas.width;
        this.height = canvas.height;
        this.radius = this.width / 2; //promien zagara

        this.isPaused = false;

        //wskazowki:
        this.hourHand = new Hand(this.radius * 0.5, 8, "#000"); //godzinowa
        this.minuteHand = new Hand(this.radius * 0.75, 5, "#000");//min
        this.secondHand = new Hand(this.radius * 0.85, 2, "red"); //sec

        this.initEvents(); //obsluga klawiatury
        this.animate();
    }
    initEvents(){
        window.addEventListener("keydown", (e) => {
            if (e.code === "Space") {
                this.isPaused = !this.isPaused;
            }
        });
    }
        drawFace() {
        const ctx = this.ctx;

        ctx.beginPath();
        ctx.arc(0, 0, this.radius - 5, 0, Math.PI * 2); //rys okrag (360st = 2π)
        ctx.lineWidth = 5;
        ctx.stroke();

        //kreski godzinowe
        for (let i = 0; i < 60; i++) {
            ctx.save();
            ctx.rotate((i * Math.PI) / 30); //obrot o 6st (360st / 60 = 6st, w radiancach p/30)

            ctx.beginPath();
            ctx.moveTo(0, -this.radius + 10);

            if (i % 5 === 0) {
                ctx.lineWidth = 4;
                ctx.lineTo(0, -this.radius + 25);
            } else {
                ctx.lineWidth = 1;
                ctx.lineTo(0, -this.radius + 18);
            }

            ctx.stroke();
            ctx.restore();
        }
    }
    drawTime() {
        const now = new Date();

        const milliseconds = now.getMilliseconds();
        const seconds = now.getSeconds() + milliseconds / 1000;
        const minutes = now.getMinutes() + seconds / 60;
        const hours = (now.getHours() % 12) + minutes / 60;

        const secondAngle = seconds * Math.PI / 30;
        const minuteAngle = minutes * Math.PI / 30;
        const hourAngle = hours * Math.PI / 6;

        this.hourHand.draw(this.ctx, hourAngle);
        this.minuteHand.draw(this.ctx, minuteAngle);
        this.secondHand.draw(this.ctx, secondAngle);
    }

    draw() {
        const ctx = this.ctx;

        ctx.fillStyle = "rgba(255, 255, 255, 0.1)";
        ctx.fillRect(0, 0, this.width, this.height);

        ctx.save();

        // Przeniesienie do środka
        ctx.translate(this.width / 2, this.height / 2);

        // Korekta -90° (bo 0 rad jest na godzinie 3)
        ctx.rotate(-Math.PI / 2);

        this.drawFace();
        this.drawTime();

        ctx.restore();
    }

    animate() {
        if (!this.isPaused) {
            this.draw();
        }

        requestAnimationFrame(() => this.animate());
    }
}

const canvas = document.getElementById("clockCanvas");
new Clock(canvas);