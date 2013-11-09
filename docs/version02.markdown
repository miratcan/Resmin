Aşağıdaki başlıklarda, version 0.2  taşına ulaşabilmek için yapılacak geliştirmeler listeleniyor.

**Cevap Gönderme Formunda Yapılacak Değişiklikler**

Kullanıcı cevap gönderirken "Kime Gözükür" (visible_for) adında bir seçenekten aşağıdaki seçeneklerden birini seçmek zorunda olacak:

 * Herkese Açık
 * Müritlerim 

**Cevap Listeleme Sayfalarında Yapılacak Değişiklikler**

"Son cevaplarım" ya da "soru detayı" sayfasına eğer kullanıcı login değil ise "Herkese Açık" olarak işaretlenmiş, "NSFW" olmayan cevapları, Eğer login ise blokladığı/bloklandığı kişilere ait olmayan, "Herkese Açık" olarak işaretlenmiş cevapları görüntüleyecek.

Eğer kullanıcı login ise sitenin navigasyon barının altına bir ek navigasyon barı gelecek bu barda aşağıdaki alt başlıklar bulunacak:

 * Umumi Cevaplar 
 * Müridi Olduklarımdan Cevaplar

Ana sayfada ya da soru detayı sayfasının kendisi aslında "Umumi Cevaplar" sayfası, eğer url sonuna '/f/' eklenir ise, (ki bunun manası from followings manasına geliyor) takip edilen kullanıcılardan gelen cevaplar listelenecek.

> Örneğin "/" sayfası herkesten, "Herkese Açık" olarak işaretlenmiş cevapları listeliyor iken "/f/" sayfası müridi olunan kişilerin müritlerim görsün diye işaretlediği cevaplarını getirecek.

> Diğer bir örnek olarak "/q/A/" sayfası bir soruya ait cevapları listeler iken, "/q/A/f/" sayfası bu soruya ait müritlerden gelen cevapları listeleyecek.

**Kullanıcının eski gönderilerine ait "Kime Gözükür" seçeneğini düzelteceği "fix-answers" adında bir ekran yazılacak**

Cevapların artık "Kime Gözükür" bilgisine sahip olması gerektiğinden bahsetmitşim. Kullanıcıların eski gönderileri bu bilgiye sahip değil. Bu yüzden ana sayfa görüntülenmeye çalıştığında önce kullanıcıya ait "Kime Gözükür" bilgisi olmayan cevapların olup olmadığınıa bakılacak. Eğer bulunabilirse "fix-answers" adında bir ekrana yönlendirilecek kullanıcı. Bu ekran:

 1. Adımı Gizle
 2. Ayıpçı
 3. Kime Gözükür

 Seçeneklerinin toplu olarka düzenlenebildiği bir ekran olacak. Kullanıcı hangi cevaba ait seçeneklerini düzenleyebildiğini anlayabilmesi için cevabın küçük resmi gösterilecek.

**Kullanıcı sayfasında değişiklikler yapılacak**

Kullanıcının kaç takipçiye sahip olduğu gösterilmesi gerekiyor bunun yanında eğer kullanıcı login değil ise bla bla bla... 
