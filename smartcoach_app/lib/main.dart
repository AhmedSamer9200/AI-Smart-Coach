import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';

// 1. دي نقطة البداية، أول حاجة بتشتغل في الأبلكيشن
void main() => runApp(SmartCoachApp());

// 2. عملنا الشاشة من نوع StatefulWidget عشان الداتا اللي فيها هتتغير كل شوية (لايف)
class SmartCoachApp extends StatefulWidget {
  @override
  _SmartCoachAppState createState() => _SmartCoachAppState();
}

class _SmartCoachAppState extends State<SmartCoachApp> {
  // 3. دي المتغيرات اللي هتشيل الداتا بتاعتنا ونعرضها على الشاشة
  String reps = "0";
  String stage = "up";
  String heartRate = "0"; 

  // 4. دالة initState بتشتغل مرة واحدة بس أول ما تفتح الشاشة
  @override
  void initState() {
    super.initState();
    // عملنا Timer ينده على دالة سحب الداتا (fetchData) كل ثانية عشان تبقى Live
    // دي تقنية اسمها Polling، ممتازة جداً ومناسبة للبروجيكت بتاعنا
    Timer.periodic(Duration(seconds: 1), (timer) {
      fetchData();
    });
  }

  // 5. دي الدالة المسئولة إنها تكلم الـ API بتاعك وتجيب الداتا
  fetchData() async {
    // 🔥 إضافة أمان (Try/Catch): عشان لو النت فصل أو السيرفر وقع، الأبلكيشن ميكراشش
    try {
      // 🔥 التعديل السحري: ربطنا الموبايل بالجلسة الموحدة اللي الكاميرا والفيتبيت شغالين عليها
      final response = await http.get(Uri.parse('https://octangular-maxim-sparkishly.ngrok-free.dev/session/smartcoach_live_session/live'));
      
      // لو الباك إند رد علينا بنجاح (كود 200)
      if (response.statusCode == 200) {
        // بنحول الرد من JSON لداتا نقدر نقراها
        var data = json.decode(response.body)['data'];
        
        // دالة setState دي أهم حاجة، دي اللي بتقول للشاشة "الداتا اتغيرت، اعملي Refresh"
        setState(() {
          reps = data['reps'].toString();
          stage = data['stage'];
          // بنسحب النبض من الداتا بيز (إحنا سجلناه في عمود emg_val)
          heartRate = data['emg'] != null ? data['emg'].toString() : "0"; 
        });
      }
    } catch (e) {
      // لو حصل أي Error في الاتصال، هيطبع المشكلة في الكونسول ومش هيقفل الأبلكيشن
      print("⚠️ مشكلة في الاتصال بالسيرفر: \$e");
    }
  }

  // 6. ده الـ Design بتاع الشاشة (الـ UI)
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false, // شيلنا شريطة الـ Debug الحمرا من فوق
      home: Scaffold(
        appBar: AppBar(
          title: Text('🏋️ SmartCoach Live'),
          backgroundColor: Colors.blueAccent,
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center, // بنوسطن الكلام في نص الشاشة
            children: [
              Text("العداد: $reps", style: TextStyle(fontSize: 40, fontWeight: FontWeight.bold)),
              SizedBox(height: 20), // مسافة فاضية
              // بنغير لون كلمة الحركة للأحمر لو اللاعب بيلعب غلط (Error)
              Text("الحركة: $stage", style: TextStyle(fontSize: 35, color: stage == "Error" ? Colors.red : Colors.blue)),
              SizedBox(height: 20),
              Text("❤️ النبض: $heartRate bpm", style: TextStyle(fontSize: 30, color: Colors.redAccent)),
            ],
          ),
        ),
      ),
    );
  }
}