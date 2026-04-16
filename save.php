<?php

$server = "localhost";
$username = "root";
$password = "";
$dbname = "chess";

$con = mysqli_connect($server ,$username ,$password ,$dbname);

if(!$con)
{
  echo "not connected";
}

$name = $_POST['full_name'];
$Number = $_POST['whatsapp'];
$Username = $_POST['username'];
$Payment_ID = $_POST['payment_id'];

$sql = "INSERT INTO `text`(`Full Name`, `WhatsApp Number`, `Lichess / Chess.com Username`, `Payment Transaction ID`) VALUES ('$name','$Number','$Username','$Payment_ID')";

$result = mysqli_query($con ,$sql);

if($result)
{
  echo "data summeted";
}

else
{
  echo "error...!";
}
?>
